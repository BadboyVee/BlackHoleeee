-- Milestone 4: creator onboarding. Applications, invite links, referral links,
-- creator profiles and payout details.
--
-- Follows the rules at the top of 20261010000000_foundation.sql: RLS on every
-- table, every grant written out (down to the column), SECURITY DEFINER
-- functions with an empty search_path that check the caller first, and helpers
-- in the private schema.
--
-- Who can do what:
--   * An applicant fills one application (public.submit_application). It also
--     fills in their profile. They read their own application, nobody else's.
--   * Staff (admin and team) read every application and approve or reject it
--     (public.review_application). Approval makes the account a creator and
--     gives them a referral code.
--   * The admin alone creates and revokes invite links. Anyone with a link can
--     check it (public.invite_preview); a signed-in applicant who redeems one
--     (public.redeem_invite) is approved straight away.
--   * Creators edit their own profile directly, except their X handle, which
--     was checked when they were approved. Payout details change only through
--     public.set_payout_details, which logs the change and emails the creator.
--     Only the creator and the admin can read payout details; team can't.
--   * Every email goes through the outbox, queued in the same transaction.

-- Lists the screens offer. Labels live in src/lib/creators/options.ts. -------------

create function private.known_niches()
returns text[]
language sql
immutable
set search_path = ''
as $$
  select array['ai', 'tech', 'crypto', 'startups', 'design', 'dev_tools', 'productivity',
               'finance', 'gaming', 'science', 'marketing', 'other']::text[]
$$;

comment on function private.known_niches() is 'The niches a creator can pick. Mirrors NICHES in src/lib/creators/options.ts.';

-- True when every item is an https link of at most 2048 characters. A missing
-- item counts as a failure, so wrap an optional column as "x is null or ...".
create function private.all_https_links(p_links text[])
returns boolean
language sql
immutable
set search_path = ''
as $$
  select coalesce(bool_and(coalesce(char_length(link) <= 2048 and link ~* '^https://[^[:space:]]+$', false)), true)
  from pg_catalog.unnest(p_links) as link
$$;

-- Eight hex characters for a referral code, sixteen for an invite. Random from
-- gen_random_uuid, so no extension is needed. Invite codes are long because a
-- valid one approves its holder.
create function private.random_code(p_length integer)
returns text
language sql
volatile
set search_path = ''
as $$
  select left(pg_catalog.replace(pg_catalog.gen_random_uuid()::text, '-', '')
              || pg_catalog.replace(pg_catalog.gen_random_uuid()::text, '-', ''), p_length)
$$;

-- Profiles: what creators tell us about themselves ---------------------------------

alter table public.profiles
  add column x_handle text check (x_handle ~ '^[A-Za-z0-9_]{1,15}$'),
  add column tiktok_url text check (tiktok_url is null or private.all_https_links(array[tiktok_url])),
  add column youtube_url text check (youtube_url is null or private.all_https_links(array[youtube_url])),
  add column instagram_url text check (instagram_url is null or private.all_https_links(array[instagram_url])),
  add column linkedin_url text check (linkedin_url is null or private.all_https_links(array[linkedin_url])),
  add column niches text[] not null default '{}'
    check (niches <@ private.known_niches() and cardinality(niches) <= 5),
  add column followers integer check (followers between 0 and 2000000000),
  add column avg_views integer check (avg_views between 0 and 2000000000),
  add column country text check (country ~ '^[A-Z]{2}$'),
  add column bio text not null default '' check (char_length(bio) <= 300),
  add column rate_per_post numeric(12, 2) check (rate_per_post >= 0),
  add column rate_currency text check (rate_currency in ('USD', 'USDC', 'USDT', 'NGN')),
  add column referral_code text unique check (referral_code ~ '^[a-f0-9]{8}$'),
  add column referred_by uuid references public.profiles (id) on delete set null,
  add constraint profiles_rate_has_currency check ((rate_per_post is null) = (rate_currency is null)),
  add constraint profiles_not_self_referred check (referred_by is distinct from id);

comment on column public.profiles.x_handle is
  'Without the @. One account per handle. Set by the application; creators can''t change it themselves.';
comment on column public.profiles.niches is 'Up to five of private.known_niches().';
comment on column public.profiles.followers is 'Self reported on X, for now.';
comment on column public.profiles.avg_views is 'Self reported average views per post, for now.';
comment on column public.profiles.country is 'ISO 3166-1 alpha-2 code, such as NG or GB.';
comment on column public.profiles.referral_code is 'Given on approval. Their link is /apply?ref=<code>.';
comment on column public.profiles.referred_by is 'The creator whose referral link they applied through.';

create unique index profiles_x_handle_key on public.profiles (lower(x_handle)) where x_handle is not null;
create index profiles_referred_by_idx on public.profiles (referred_by) where referred_by is not null;

-- Creators edit these themselves. Role, status, email, X handle, referral code
-- and referrer never are.
grant update (
  tiktok_url, youtube_url, instagram_url, linkedin_url, niches, followers, avg_views,
  country, bio, rate_per_post, rate_currency
) on table public.profiles to authenticated;

-- Invites --------------------------------------------------------------------------

create table public.invites (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code ~ '^[a-f0-9]{16}$'),
  label text not null default '' check (char_length(label) <= 80),
  max_uses integer check (max_uses between 1 and 10000),
  uses integer not null default 0 check (uses >= 0),
  expires_at timestamptz,
  revoked_at timestamptz,
  created_by uuid references public.profiles (id) on delete set null,
  created_at timestamptz not null default now(),
  check (max_uses is null or uses <= max_uses)
);

comment on table public.invites is
  'Invite links (/invite/<code>) that approve a new creator straight away. Admin only. '
  'Created and revoked through database functions.';
comment on column public.invites.label is 'Where the link went, such as "Telegram group". Only the admin sees it.';

create index invites_created_at_idx on public.invites (created_at desc);

alter table public.invites enable row level security;

revoke all on table public.invites from anon, authenticated, service_role;
grant select on table public.invites to authenticated, service_role;

create policy "Admin reads invites"
  on public.invites for select to authenticated
  using ((select private.is_admin()));

-- Applications ---------------------------------------------------------------------

create type public.application_status as enum ('submitted', 'approved', 'rejected');

create table public.applications (
  id uuid primary key default gen_random_uuid(),
  applicant uuid not null unique references public.profiles (id) on delete cascade,
  status public.application_status not null default 'submitted',
  best_posts text[] check (cardinality(best_posts) between 1 and 3 and private.all_https_links(best_posts)),
  why text check (char_length(btrim(why)) between 20 and 1000),
  referred_by uuid references public.profiles (id) on delete set null,
  invite_id uuid references public.invites (id) on delete set null,
  reviewed_by uuid references public.profiles (id) on delete set null,
  reviewed_at timestamptz,
  review_note text not null default '' check (char_length(review_note) <= 2000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Invited creators skip the questions; everyone else answers them.
  check (invite_id is not null or (best_posts is not null and why is not null)),
  check ((status = 'submitted') = (reviewed_at is null))
);

comment on table public.applications is
  'One per person: their answers and where it stands. Written only by database functions. '
  'An invited creator gets an approved row with no answers.';
comment on column public.applications.review_note is 'Private staff notes. Never shown to the applicant.';

create index applications_status_created_at_idx on public.applications (status, created_at desc);

create trigger applications_touch_updated_at
  before update on public.applications
  for each row execute function private.touch_updated_at();

alter table public.applications enable row level security;

revoke all on table public.applications from anon, authenticated, service_role;
grant select on table public.applications to authenticated, service_role;

create policy "Applicants read their own application"
  on public.applications for select to authenticated
  using (applicant = (select auth.uid()));

create policy "Staff read every application"
  on public.applications for select to authenticated
  using ((select private.is_staff()));

-- Payout details ---------------------------------------------------------------------

create type public.payout_method as enum ('crypto', 'bank', 'other');

create table public.payout_details (
  profile_id uuid primary key references public.profiles (id) on delete cascade,
  method public.payout_method not null,
  crypto_asset text check (crypto_asset in ('USDC', 'USDT')),
  crypto_network text check (crypto_network in ('base', 'solana', 'ethereum', 'polygon', 'arbitrum', 'tron')),
  wallet_address text,
  bank_country text check (bank_country ~ '^[A-Z]{2}$'),
  bank_name text check (char_length(btrim(bank_name)) between 1 and 120),
  account_name text check (char_length(btrim(account_name)) between 1 and 120),
  account_number text check (account_number ~ '^[A-Za-z0-9 -]{4,40}$'),
  bank_code text check (char_length(bank_code) <= 40),
  other_details text check (char_length(btrim(other_details)) between 1 and 500),
  updated_at timestamptz not null default now(),
  check (
    (method = 'crypto'
      and crypto_asset is not null and crypto_network is not null and wallet_address is not null
      and bank_country is null and bank_name is null and account_name is null and account_number is null
      and bank_code is null and other_details is null)
    or (method = 'bank'
      and bank_country is not null and bank_name is not null and account_name is not null and account_number is not null
      and crypto_asset is null and crypto_network is null and wallet_address is null and other_details is null)
    or (method = 'other'
      and other_details is not null
      and crypto_asset is null and crypto_network is null and wallet_address is null
      and bank_country is null and bank_name is null and account_name is null and account_number is null
      and bank_code is null)
  ),
  -- The address must suit its network, so a payment never goes to a malformed one.
  check (
    wallet_address is null
    or (crypto_network in ('base', 'ethereum', 'polygon', 'arbitrum') and wallet_address ~ '^0x[0-9a-fA-F]{40}$')
    or (crypto_network = 'solana' and wallet_address ~ '^[1-9A-HJ-NP-Za-km-z]{32,44}$')
    or (crypto_network = 'tron' and wallet_address ~ '^T[1-9A-HJ-NP-Za-km-z]{33}$')
  ),
  -- Only the stablecoins we send on each network: no USDT on Base, no USDC on Tron.
  check (not (crypto_asset = 'USDT' and crypto_network = 'base') and not (crypto_asset = 'USDC' and crypto_network = 'tron'))
);

comment on table public.payout_details is
  'Where a creator wants to be paid. Only they and the admin can read it (team can''t). '
  'Changed only through public.set_payout_details, which logs it and emails the creator.';

create trigger payout_details_touch_updated_at
  before update on public.payout_details
  for each row execute function private.touch_updated_at();

alter table public.payout_details enable row level security;

revoke all on table public.payout_details from anon, authenticated, service_role;
grant select on table public.payout_details to authenticated;

create policy "Creators read their own payout details"
  on public.payout_details for select to authenticated
  using (profile_id = (select auth.uid()));

create policy "Admin reads payout details"
  on public.payout_details for select to authenticated
  using ((select private.is_admin()));

-- The outbox learns the creator emails ------------------------------------------------

comment on column public.outbox.template is
  'Which message to build: lead_received, application_received, application_approved, '
  'application_rejected or payout_details_changed.';

-- Helpers -------------------------------------------------------------------------------

-- Gives a creator a referral code, once. Retries the rare clash.
create function private.assign_referral_code(p_profile uuid)
returns text
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_code text;
begin
  select p.referral_code into v_code from public.profiles p where p.id = p_profile;
  if v_code is not null then
    return v_code;
  end if;
  for attempt in 1..10 loop
    begin
      update public.profiles p
      set referral_code = private.random_code(8)
      where p.id = p_profile and p.referral_code is null
      returning p.referral_code into v_code;
      return v_code;
    exception when unique_violation then
      null; -- Another creator has that code. Pick again.
    end;
  end loop;
  raise exception 'Could not find a free referral code';
end;
$$;

-- Queues an email to a profile's address, adding profile_id to the payload so
-- the email can be built from the profile. Returns the outbox row, or null when
-- the profile has no usable address.
create function private.queue_profile_email(p_profile uuid, p_template text, p_payload jsonb)
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_email text;
  v_id uuid;
begin
  select p.email into v_email from public.profiles p where p.id = p_profile;
  if v_email is null or v_email !~ '^[^@[:space:]]+@[^@[:space:]]+$' or char_length(v_email) > 254 then
    return null;
  end if;
  insert into public.outbox (channel, recipient, template, payload)
  values ('email', v_email, p_template, coalesce(p_payload, '{}'::jsonb) || pg_catalog.jsonb_build_object('profile_id', p_profile))
  returning id into v_id;
  return v_id;
end;
$$;

-- Makes an applicant a creator: the role, a referral code and the log.
create function private.approve_profile(p_profile uuid, p_actor uuid, p_via text)
returns void
language plpgsql
volatile
security definer
set search_path = ''
as $$
begin
  update public.profiles p
  set role = 'creator'
  where p.id = p_profile and p.role = 'applicant';
  perform private.assign_referral_code(p_profile);
  perform private.log_activity(
    p_actor,
    'profile.role_changed',
    'profile',
    p_profile::text,
    pg_catalog.jsonb_build_object('role', 'creator', 'via', p_via)
  );
end;
$$;

revoke all on function private.known_niches() from public, anon, authenticated, service_role;
revoke all on function private.all_https_links(text[]) from public, anon, authenticated, service_role;
revoke all on function private.random_code(integer) from public, anon, authenticated, service_role;
revoke all on function private.assign_referral_code(uuid) from public, anon, authenticated, service_role;
revoke all on function private.queue_profile_email(uuid, text, jsonb) from public, anon, authenticated, service_role;
revoke all on function private.approve_profile(uuid, uuid, text) from public, anon, authenticated, service_role;

-- The check constraints call these, so the roles that write those columns need them.
grant execute on function private.known_niches() to authenticated, service_role;
grant execute on function private.all_https_links(text[]) to authenticated, service_role;

-- Applying --------------------------------------------------------------------------

create function public.submit_application(
  p_display_name text,
  p_x_handle text,
  p_tiktok_url text,
  p_youtube_url text,
  p_instagram_url text,
  p_linkedin_url text,
  p_niches text[],
  p_followers integer,
  p_avg_views integer,
  p_country text,
  p_best_posts text[],
  p_why text,
  p_referral_code text
)
returns table (application_id uuid, outbox_id uuid)
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_me uuid := (select auth.uid());
  v_referrer uuid;
begin
  if v_me is null or private.current_user_role() is distinct from 'applicant' then
    raise exception 'Only applicants can apply' using errcode = '42501';
  end if;
  if exists (select 1 from public.applications a where a.applicant = v_me) then
    raise exception 'already_applied' using errcode = 'P0409';
  end if;

  -- A referral code counts when it belongs to an active creator who isn't the applicant.
  if nullif(btrim(p_referral_code), '') is not null then
    select p.id into v_referrer
    from public.profiles p
    where p.referral_code = lower(btrim(p_referral_code))
      and p.role = 'creator' and p.status = 'active' and p.id <> v_me;
  end if;

  update public.profiles p
  set display_name = btrim(p_display_name),
      x_handle = nullif(btrim(p_x_handle), ''),
      tiktok_url = nullif(btrim(p_tiktok_url), ''),
      youtube_url = nullif(btrim(p_youtube_url), ''),
      instagram_url = nullif(btrim(p_instagram_url), ''),
      linkedin_url = nullif(btrim(p_linkedin_url), ''),
      niches = coalesce(p_niches, '{}'),
      followers = p_followers,
      avg_views = p_avg_views,
      country = upper(btrim(p_country)),
      referred_by = coalesce(v_referrer, p.referred_by)
  where p.id = v_me;

  insert into public.applications (applicant, best_posts, why, referred_by)
  values (v_me, p_best_posts, btrim(p_why), v_referrer)
  returning id into application_id;

  insert into public.outbox (channel, recipient, template, payload)
  values ('email', 'owner', 'application_received', pg_catalog.jsonb_build_object('application_id', application_id))
  returning id into outbox_id;

  perform private.log_activity(
    v_me,
    'application.submitted',
    'application',
    application_id::text,
    pg_catalog.jsonb_build_object('referred', v_referrer is not null)
  );

  return next;
end;
$$;

comment on function public.submit_application(text, text, text, text, text, text, text[], integer, integer, text, text[], text, text) is
  'An applicant''s one application: fills in their profile, saves the answers, notes who '
  'referred them (when the code belongs to an active creator), emails the owner and logs it. '
  'Raises already_applied (P0409) the second time.';

create function public.review_application(p_application uuid, p_decision text, p_note text default '')
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_me uuid := (select auth.uid());
  v_application public.applications;
  v_outbox uuid;
begin
  if not private.is_staff() then
    raise exception 'Only staff can review applications' using errcode = '42501';
  end if;
  if p_decision is null or p_decision not in ('approve', 'reject') then
    raise exception 'The decision is approve or reject' using errcode = '22023';
  end if;

  select * into v_application from public.applications a where a.id = p_application for update;
  if not found then
    raise exception 'No such application' using errcode = 'P0002';
  end if;
  if v_application.status <> 'submitted' then
    raise exception 'already_reviewed' using errcode = 'P0409';
  end if;

  update public.applications a
  set status = case when p_decision = 'approve' then 'approved' else 'rejected' end::public.application_status,
      reviewed_by = v_me,
      reviewed_at = now(),
      review_note = left(coalesce(btrim(p_note), ''), 2000)
  where a.id = p_application;

  if p_decision = 'approve' then
    perform private.approve_profile(v_application.applicant, v_me, 'application');
  end if;

  v_outbox := private.queue_profile_email(
    v_application.applicant,
    case when p_decision = 'approve' then 'application_approved' else 'application_rejected' end,
    pg_catalog.jsonb_build_object('application_id', p_application)
  );

  perform private.log_activity(
    v_me,
    case when p_decision = 'approve' then 'application.approved' else 'application.rejected' end,
    'application',
    p_application::text,
    '{}'::jsonb
  );

  return v_outbox;
end;
$$;

comment on function public.review_application(uuid, text, text) is
  'Staff approve or reject a submitted application, with private notes. Approval makes the '
  'applicant a creator with a referral code. Emails the applicant and logs it. Returns the '
  'outbox row. Raises already_reviewed (P0409) for an application that isn''t waiting.';

-- Invites ---------------------------------------------------------------------------

create function public.create_invite(p_label text default '', p_max_uses integer default null, p_expires_at timestamptz default null)
returns public.invites
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_invite public.invites;
begin
  if not private.is_admin() then
    raise exception 'Only the admin can create invite links' using errcode = '42501';
  end if;
  if p_expires_at is not null and p_expires_at <= now() then
    raise exception 'The expiry has to be in the future' using errcode = '22023';
  end if;

  insert into public.invites (code, label, max_uses, expires_at, created_by)
  values (private.random_code(16), coalesce(btrim(p_label), ''), p_max_uses, p_expires_at, (select auth.uid()))
  returning * into v_invite;

  perform private.log_activity(
    (select auth.uid()),
    'invite.created',
    'invite',
    v_invite.id::text,
    pg_catalog.jsonb_build_object('max_uses', p_max_uses, 'expires_at', p_expires_at)
  );
  return v_invite;
end;
$$;

create function public.revoke_invite(p_invite uuid)
returns void
language plpgsql
volatile
security definer
set search_path = ''
as $$
begin
  if not private.is_admin() then
    raise exception 'Only the admin can revoke invite links' using errcode = '42501';
  end if;
  update public.invites i set revoked_at = now() where i.id = p_invite and i.revoked_at is null;
  if found then
    perform private.log_activity((select auth.uid()), 'invite.revoked', 'invite', p_invite::text, '{}'::jsonb);
  end if;
end;
$$;

-- Where an invite code stands: valid, revoked, expired, used_up or unknown.
create function private.invite_state(p_invite public.invites)
returns text
language sql
stable
set search_path = ''
as $$
  select case
    when p_invite.id is null then 'unknown'
    when p_invite.revoked_at is not null then 'revoked'
    when p_invite.expires_at is not null and p_invite.expires_at <= now() then 'expired'
    when p_invite.max_uses is not null and p_invite.uses >= p_invite.max_uses then 'used_up'
    else 'valid'
  end
$$;

revoke all on function private.invite_state(public.invites) from public, anon, authenticated, service_role;

create function public.invite_preview(p_code text)
returns text
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_invite public.invites;
begin
  select * into v_invite from public.invites i where i.code = lower(btrim(p_code));
  return private.invite_state(v_invite);
end;
$$;

comment on function public.invite_preview(text) is
  'Says whether an invite code is valid, revoked, expired, used_up or unknown, and nothing '
  'else. Anyone can ask: the invite page uses it before sign up.';

create function public.redeem_invite(p_code text)
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_me uuid := (select auth.uid());
  v_invite public.invites;
  v_state text;
  v_outbox uuid;
begin
  if v_me is null or private.current_user_role() is distinct from 'applicant' then
    raise exception 'Only applicants can use an invite' using errcode = '42501';
  end if;

  select * into v_invite from public.invites i where i.code = lower(btrim(p_code)) for update;
  v_state := private.invite_state(v_invite);
  if v_state <> 'valid' then
    raise exception 'invite_%', v_state using errcode = 'P0410';
  end if;

  update public.invites i set uses = i.uses + 1 where i.id = v_invite.id;

  -- An application already waiting is approved through the invite; otherwise one is recorded.
  insert into public.applications (applicant, status, invite_id, reviewed_at)
  values (v_me, 'approved', v_invite.id, now())
  on conflict (applicant) do update
    set status = 'approved',
        invite_id = excluded.invite_id,
        reviewed_at = coalesce(public.applications.reviewed_at, now()),
        reviewed_by = null;

  perform private.approve_profile(v_me, v_me, 'invite');
  v_outbox := private.queue_profile_email(
    v_me,
    'application_approved',
    pg_catalog.jsonb_build_object('invite_id', v_invite.id)
  );
  perform private.log_activity(v_me, 'invite.redeemed', 'invite', v_invite.id::text, '{}'::jsonb);
  return v_outbox;
end;
$$;

comment on function public.redeem_invite(text) is
  'A signed-in applicant uses an invite link: counts the use, approves them (role creator, '
  'referral code), emails a welcome and logs it. Raises invite_<state> (P0410) for an invite '
  'that is revoked, expired, used up or unknown. Returns the outbox row.';

-- Payout details --------------------------------------------------------------------

create function public.set_payout_details(
  p_method text,
  p_crypto_asset text default null,
  p_crypto_network text default null,
  p_wallet_address text default null,
  p_bank_country text default null,
  p_bank_name text default null,
  p_account_name text default null,
  p_account_number text default null,
  p_bank_code text default null,
  p_other_details text default null
)
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_me uuid := (select auth.uid());
  v_method public.payout_method;
  v_summary text;
  v_outbox uuid;
begin
  if v_me is null or private.current_user_role() is distinct from 'creator' then
    raise exception 'Only creators can set payout details' using errcode = '42501';
  end if;
  if p_method is null or p_method not in ('crypto', 'bank', 'other') then
    raise exception 'The method is crypto, bank or other' using errcode = '22023';
  end if;
  v_method := p_method::public.payout_method;

  -- Only the fields of the chosen method are kept; the table's checks do the rest.
  insert into public.payout_details as d (
    profile_id, method, crypto_asset, crypto_network, wallet_address, bank_country, bank_name,
    account_name, account_number, bank_code, other_details
  )
  values (
    v_me,
    v_method,
    case when v_method = 'crypto' then upper(btrim(p_crypto_asset)) end,
    case when v_method = 'crypto' then lower(btrim(p_crypto_network)) end,
    case when v_method = 'crypto' then btrim(p_wallet_address) end,
    case when v_method = 'bank' then upper(btrim(p_bank_country)) end,
    case when v_method = 'bank' then btrim(p_bank_name) end,
    case when v_method = 'bank' then btrim(p_account_name) end,
    case when v_method = 'bank' then btrim(p_account_number) end,
    case when v_method = 'bank' then nullif(btrim(p_bank_code), '') end,
    case when v_method = 'other' then btrim(p_other_details) end
  )
  on conflict (profile_id) do update set
    method = excluded.method,
    crypto_asset = excluded.crypto_asset,
    crypto_network = excluded.crypto_network,
    wallet_address = excluded.wallet_address,
    bank_country = excluded.bank_country,
    bank_name = excluded.bank_name,
    account_name = excluded.account_name,
    account_number = excluded.account_number,
    bank_code = excluded.bank_code,
    other_details = excluded.other_details;

  -- A masked summary for the email, so the creator can recognise the change.
  v_summary := case v_method
    when 'crypto' then upper(btrim(p_crypto_asset)) || ' on ' || initcap(btrim(p_crypto_network))
      || ', wallet ending ' || right(btrim(p_wallet_address), 4)
    -- Spaces and dashes people type in an IBAN don't count, so this matches the profile page.
    when 'bank' then btrim(p_bank_name) || ', account ending '
      || right(pg_catalog.regexp_replace(btrim(p_account_number), '[[:space:]-]+', '', 'g'), 4)
    else 'Other: see your profile'
  end;

  v_outbox := private.queue_profile_email(
    v_me,
    'payout_details_changed',
    pg_catalog.jsonb_build_object('summary', v_summary)
  );
  perform private.log_activity(v_me, 'payout_details.changed', 'profile', v_me::text,
    pg_catalog.jsonb_build_object('method', p_method));
  return v_outbox;
end;
$$;

comment on function public.set_payout_details(text, text, text, text, text, text, text, text, text, text) is
  'A creator saves where they want to be paid. Keeps only the chosen method''s fields, logs '
  'the change (never the details) and emails the creator a masked summary, so nobody can '
  'quietly swap them. Returns the outbox row.';

-- Referrals --------------------------------------------------------------------------

create function public.my_referrals()
returns table (applied integer, approved integer)
language sql
stable
security definer
set search_path = ''
as $$
  select
    count(*)::integer,
    count(*) filter (where p.role in ('creator', 'team', 'admin'))::integer
  from public.profiles p
  where p.referred_by = (select auth.uid())
$$;

comment on function public.my_referrals() is
  'How many people applied with the caller''s referral link, and how many of them were approved.';

-- Who can call what ---------------------------------------------------------------------

revoke all on function public.submit_application(text, text, text, text, text, text, text[], integer, integer, text, text[], text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.review_application(uuid, text, text) from public, anon, authenticated, service_role;
revoke all on function public.create_invite(text, integer, timestamptz) from public, anon, authenticated, service_role;
revoke all on function public.revoke_invite(uuid) from public, anon, authenticated, service_role;
revoke all on function public.invite_preview(text) from public, anon, authenticated, service_role;
revoke all on function public.redeem_invite(text) from public, anon, authenticated, service_role;
revoke all on function public.set_payout_details(text, text, text, text, text, text, text, text, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.my_referrals() from public, anon, authenticated, service_role;

-- Each function checks its caller's role itself.
grant execute on function public.submit_application(text, text, text, text, text, text, text[], integer, integer, text, text[], text, text)
  to authenticated;
grant execute on function public.review_application(uuid, text, text) to authenticated;
grant execute on function public.create_invite(text, integer, timestamptz) to authenticated;
grant execute on function public.revoke_invite(uuid) to authenticated;
grant execute on function public.invite_preview(text) to anon, authenticated;
grant execute on function public.redeem_invite(text) to authenticated;
grant execute on function public.set_payout_details(text, text, text, text, text, text, text, text, text, text)
  to authenticated;
grant execute on function public.my_referrals() to authenticated;
