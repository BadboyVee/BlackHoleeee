-- Milestone 2: "Book a campaign" leads, the email outbox, the activity log and
-- rate limits.
--
-- Follows the rules at the top of 20261010000000_foundation.sql: RLS on every
-- table, every grant written out (down to the column), SECURITY DEFINER
-- functions with an empty search_path and fully qualified names, and helpers in
-- the private schema.
--
-- Who can do what:
--   * Visitors never touch these tables. The site's server saves a booking by
--     calling public.submit_lead with the service key, after its own checks
--     (zod, honeypot, fill time).
--   * Staff (admin and team) read leads, the outbox and the activity log, and
--     can change a lead's status and notes. Nothing else.
--   * The service key (service_role) runs the outbox worker through
--     public.claim_outbox and public.finish_outbox, and reads leads and the
--     outbox to build each email. It writes the activity log only through
--     database functions, like everyone else.
--
-- Supabase grants anon, authenticated and service_role everything on new
-- objects in public by default (or nothing, when a project turns that off).
-- So each table and function below first revokes everything from all three,
-- then grants exactly what is needed. The same migration works either way.

-- Types ----------------------------------------------------------------------------

create type public.lead_status as enum ('new', 'contacted', 'won', 'lost');
create type public.budget_range as enum ('under_5k', '5k_10k', '10k_25k', '25k_plus', 'not_sure');

comment on type public.lead_status is 'Where a lead stands in the sales pipeline.';
comment on type public.budget_range is
  'Budget ranges offered on the Book a campaign form. Labels live in src/lib/leads/booking.ts.';

-- Leads ----------------------------------------------------------------------------
-- Length limits mirror LIMITS in src/lib/leads/booking.ts. The form's zod
-- schema is stricter; these are the last line of defense.

create table public.leads (
  id uuid primary key default gen_random_uuid(),
  name text not null check (btrim(name) <> '' and char_length(name) <= 80),
  email text not null check (
    char_length(email) <= 254 and email ~ '^[^@[:space:]]+@[^@[:space:]]+$'
  ),
  company text not null check (btrim(company) <> '' and char_length(company) <= 120),
  website text check (
    char_length(website) <= 2048 and website ~* '^https?://[^[:space:]]+$'
  ),
  x_handle text check (x_handle ~ '^[A-Za-z0-9_]{1,15}$'),
  launching text not null check (btrim(launching) <> '' and char_length(launching) <= 600),
  launch_date date,
  budget public.budget_range not null,
  message text check (char_length(message) <= 2000),
  source text not null check (source in ('book_page', 'home_cta')),
  status public.lead_status not null default 'new',
  notes text not null default '' check (char_length(notes) <= 5000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.leads is
  'Book a campaign requests from the public site. Created only by public.submit_lead. '
  'Staff read them and move them through new, contacted, won and lost, with private notes.';
comment on column public.leads.source is 'Where the form was sent from: the /book page or the home page.';
comment on column public.leads.notes is 'Private staff notes. Never shown to the person who booked.';

create index leads_created_at_idx on public.leads (created_at desc);
create index leads_status_created_at_idx on public.leads (status, created_at desc);

create trigger leads_touch_updated_at
  before update on public.leads
  for each row execute function private.touch_updated_at();

alter table public.leads enable row level security;

revoke all on table public.leads from anon, authenticated, service_role;
grant select on table public.leads to authenticated;
-- Staff can move a lead along and keep notes. What the person sent never changes.
grant update (status, notes) on table public.leads to authenticated;
-- The outbox worker reads a lead to write the owner's email.
grant select on table public.leads to service_role;

create policy "Staff read leads"
  on public.leads for select to authenticated
  using ((select private.is_staff()));

create policy "Staff update leads"
  on public.leads for update to authenticated
  using ((select private.is_staff()))
  with check ((select private.is_staff()));

-- Outbox ---------------------------------------------------------------------------
-- Emails (and later Telegram posts) wait here until a worker sends them, so a
-- slow or broken provider delays a message instead of losing it.

create table public.outbox (
  id uuid primary key default gen_random_uuid(),
  channel text not null default 'email' check (channel in ('email')),
  recipient text not null check (
    recipient = 'owner'
    or (char_length(recipient) <= 254 and recipient ~ '^[^@[:space:]]+@[^@[:space:]]+$')
  ),
  template text not null check (template ~ '^[a-z][a-z0-9_.-]{0,63}$'),
  payload jsonb not null default '{}'::jsonb check (jsonb_typeof(payload) = 'object'),
  status text not null default 'pending' check (status in ('pending', 'sending', 'sent', 'failed')),
  attempts integer not null default 0 check (attempts >= 0),
  last_error text check (char_length(last_error) <= 2000),
  send_after timestamptz not null default now(),
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((status = 'sent') = (sent_at is not null))
);

comment on table public.outbox is
  'Messages waiting to be sent. Database functions add rows; the worker claims them with '
  'public.claim_outbox, sends them, and reports back with public.finish_outbox. '
  'Failed sends retry with a growing delay and give up after 5 attempts.';
comment on column public.outbox.recipient is
  'Who gets it: ''owner'' (the agency inbox in LEADS_NOTIFY_EMAIL) or an email address.';
comment on column public.outbox.template is 'Which message to build, such as lead_received.';
comment on column public.outbox.payload is 'Ids the template needs, such as {"lead_id": "..."}. Never secrets.';
comment on column public.outbox.attempts is 'How many times a worker has claimed this row.';
comment on column public.outbox.send_after is 'Not sent before this time. Pushed back after each failure.';
comment on column public.outbox.updated_at is
  'Last change. For a row that is sending, this is when it was claimed.';

-- What claim_outbox looks for: due rows, and sends that stalled.
create index outbox_due_idx on public.outbox (send_after) where status = 'pending';
create index outbox_sending_idx on public.outbox (updated_at) where status = 'sending';

create trigger outbox_touch_updated_at
  before update on public.outbox
  for each row execute function private.touch_updated_at();

alter table public.outbox enable row level security;

revoke all on table public.outbox from anon, authenticated, service_role;
grant select on table public.outbox to authenticated;
-- The worker reads rows; it changes them only through claim_outbox and finish_outbox.
grant select on table public.outbox to service_role;

create policy "Staff read the outbox"
  on public.outbox for select to authenticated
  using ((select private.is_staff()));

-- Activity log ---------------------------------------------------------------------
-- Insert-only. Rows come from database functions (through private.log_activity),
-- never from a direct insert, so nobody can forge or erase history.

create table public.activity_log (
  id bigint generated always as identity primary key,
  actor uuid,
  action text not null check (action ~ '^[a-z][a-z0-9_.]{0,63}$'),
  entity_type text check (char_length(entity_type) between 1 and 64),
  entity_id text check (char_length(entity_id) between 1 and 128),
  details jsonb not null default '{}'::jsonb check (jsonb_typeof(details) = 'object'),
  created_at timestamptz not null default now()
);

comment on table public.activity_log is
  'Who did what, and when. Written only by database functions; staff can read it. '
  'Nobody can change or delete a row.';
comment on column public.activity_log.actor is
  'The signed-in user who did it, or null for the public site and the system. '
  'No foreign key, so history stays intact if an account is deleted.';
comment on column public.activity_log.action is 'What happened, as noun.verb, such as lead.created.';

create index activity_log_created_at_idx on public.activity_log (created_at desc);
create index activity_log_entity_idx on public.activity_log (entity_type, entity_id, created_at desc);

alter table public.activity_log enable row level security;

revoke all on table public.activity_log from anon, authenticated, service_role;
revoke all on sequence public.activity_log_id_seq from anon, authenticated, service_role;
grant select on table public.activity_log to authenticated, service_role;

create policy "Staff read the activity log"
  on public.activity_log for select to authenticated
  using ((select private.is_staff()));

-- Rate limits ----------------------------------------------------------------------
-- One counter per bucket per fixed time window. Only private.take_rate_limit
-- touches it; no role has any privilege on it.

create table public.rate_limits (
  bucket text not null check (char_length(bucket) between 1 and 200),
  window_start timestamptz not null,
  hits integer not null default 0 check (hits >= 0),
  primary key (bucket, window_start)
);

comment on table public.rate_limits is
  'Counters for rate limits, such as Book a campaign requests per visitor. '
  'Used only by private.take_rate_limit. No API access.';
comment on column public.rate_limits.bucket is
  'What is being limited and for whom, such as lead:<salted hash of the IP>. Never a raw IP.';

alter table public.rate_limits enable row level security;

revoke all on table public.rate_limits from anon, authenticated, service_role;

-- Helpers --------------------------------------------------------------------------

create function private.take_rate_limit(p_bucket text, p_limit integer, p_window interval)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_window_start timestamptz;
  v_hits integer;
begin
  if p_bucket is null or p_limit is null or p_window is null or p_window <= interval '0' then
    raise exception 'take_rate_limit needs a bucket, a limit and a positive window'
      using errcode = '22023';
  end if;

  -- Fixed windows lined up with the epoch: for one hour, each clock hour in UTC.
  v_window_start := pg_catalog.date_bin(p_window, now(), timestamptz '1970-01-01 00:00:00+00');

  insert into public.rate_limits as r (bucket, window_start, hits)
  values (p_bucket, v_window_start, 1)
  on conflict (bucket, window_start) do update set hits = r.hits + 1
  returning r.hits into v_hits;

  -- Earlier windows for this bucket no longer matter.
  delete from public.rate_limits r
  where r.bucket = p_bucket and r.window_start < v_window_start;

  return v_hits <= p_limit;
end;
$$;

comment on function private.take_rate_limit(text, integer, interval) is
  'Counts one hit for a bucket and says whether it is still within p_limit hits for the '
  'current window (true = allowed). Windows are fixed and line up with the clock, so one '
  'hour means each hour in UTC. Safe under concurrent calls.';

create function private.log_activity(
  p_actor uuid,
  p_action text,
  p_entity_type text,
  p_entity_id text,
  p_details jsonb default '{}'::jsonb
)
returns void
language sql
volatile
security definer
set search_path = ''
as $$
  insert into public.activity_log (actor, action, entity_type, entity_id, details)
  values (p_actor, p_action, p_entity_type, p_entity_id, coalesce(p_details, '{}'::jsonb));
$$;

comment on function private.log_activity(uuid, text, text, text, jsonb) is
  'Adds one row to the activity log. For other database functions only.';

revoke all on function private.take_rate_limit(text, integer, interval) from public, anon, authenticated, service_role;
revoke all on function private.log_activity(uuid, text, text, text, jsonb) from public, anon, authenticated, service_role;

-- Book a campaign ------------------------------------------------------------------

create function public.submit_lead(
  p_name text,
  p_email text,
  p_company text,
  p_website text,
  p_x_handle text,
  p_launching text,
  p_launch_date date,
  p_budget text,
  p_message text,
  p_source text,
  p_rate_key text
)
returns table (lead_id uuid, outbox_id uuid)
language plpgsql
volatile
security definer
set search_path = ''
as $$
begin
  -- The server passes a salted hash of the visitor's IP. Without one, every
  -- such request shares a single bucket rather than escaping the limit.
  if not private.take_rate_limit(
    'lead:' || left(coalesce(nullif(btrim(p_rate_key), ''), 'unknown'), 128),
    5,
    interval '1 hour'
  ) then
    raise exception 'rate_limited'
      using errcode = 'P0429',
            hint = 'At most 5 booking requests per hour from one connection.';
  end if;

  insert into public.leads (
    name, email, company, website, x_handle, launching, launch_date, budget, message, source
  )
  values (
    btrim(p_name),
    btrim(p_email),
    btrim(p_company),
    nullif(btrim(p_website), ''),
    nullif(btrim(p_x_handle), ''),
    btrim(p_launching),
    p_launch_date,
    p_budget::public.budget_range,
    nullif(btrim(p_message), ''),
    p_source
  )
  returning id into lead_id;

  insert into public.outbox (channel, recipient, template, payload)
  values ('email', 'owner', 'lead_received', pg_catalog.jsonb_build_object('lead_id', lead_id))
  returning id into outbox_id;

  perform private.log_activity(
    null,
    'lead.created',
    'lead',
    lead_id::text,
    pg_catalog.jsonb_build_object('source', p_source, 'company', btrim(p_company))
  );

  return next;
end;
$$;

comment on function public.submit_lead(text, text, text, text, text, text, date, text, text, text, text) is
  'Saves a Book a campaign request in one transaction: checks the rate limit (5 per hour per '
  'p_rate_key, else error rate_limited with code P0429), inserts the lead, queues the '
  'lead_received email to the owner and logs lead.created. Service key only: the site''s '
  'server validates the form first.';

-- Outbox worker --------------------------------------------------------------------

create function public.claim_outbox(p_limit integer default 10, p_id uuid default null)
returns setof public.outbox
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  stale_before timestamptz := now() - interval '15 minutes';
begin
  -- A send that stalled on its last allowed attempt will never finish: give up on it.
  update public.outbox o
  set status = 'failed',
      last_error = left(
        coalesce(o.last_error || ' ', '') || 'Gave up: the last attempt never reported back.',
        2000
      )
  where o.id in (
    select s.id
    from public.outbox s
    where s.status = 'sending' and s.updated_at < stale_before and s.attempts >= 5
      and (p_id is null or s.id = p_id)
    for update skip locked
  );

  -- Due rows, plus sends that stalled with attempts left. Rows another worker
  -- holds right now are skipped, so two workers never send the same message.
  return query
  with picked as (
    select o.id
    from public.outbox o
    where (p_id is null or o.id = p_id)
      and (
        (o.status = 'pending' and o.send_after <= now())
        or (o.status = 'sending' and o.updated_at < stale_before and o.attempts < 5)
      )
    order by o.send_after, o.created_at
    limit least(greatest(coalesce(p_limit, 10), 0), 100)
    for update skip locked
  )
  update public.outbox o
  set status = 'sending',
      attempts = o.attempts + 1
  from picked
  where o.id = picked.id
  returning o.*;
end;
$$;

comment on function public.claim_outbox(integer, uuid) is
  'Hands the worker up to p_limit messages to send (at most 100), or just p_id: rows that are '
  'pending and due, and rows stuck sending for over 15 minutes. Marks them sending and counts '
  'the attempt. Skips rows another worker holds. Service key only.';

create function public.finish_outbox(p_id uuid, p_ok boolean, p_error text default null)
returns void
language plpgsql
volatile
security definer
set search_path = ''
as $$
begin
  if coalesce(p_ok, false) then
    update public.outbox o
    set status = 'sent', sent_at = now()
    where o.id = p_id and o.status = 'sending';
  else
    update public.outbox o
    set status = case when o.attempts >= 5 then 'failed' else 'pending' end,
        send_after = case
          when o.attempts >= 5 then o.send_after
          else now() + pg_catalog.make_interval(mins => o.attempts * o.attempts)
        end,
        last_error = left(coalesce(nullif(btrim(p_error), ''), 'Unknown error.'), 2000)
    where o.id = p_id and o.status = 'sending';
  end if;
  -- A row that isn't sending (already finished, or never claimed) is left alone.
end;
$$;

comment on function public.finish_outbox(uuid, boolean, text) is
  'Records how a send went. Success marks the row sent. A failure retries after attempts '
  'squared minutes (1, 4, 9, 16), and after the 5th attempt marks it failed. Only changes '
  'rows that are sending. Service key only.';

revoke all on function public.submit_lead(text, text, text, text, text, text, date, text, text, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.claim_outbox(integer, uuid) from public, anon, authenticated, service_role;
revoke all on function public.finish_outbox(uuid, boolean, text) from public, anon, authenticated, service_role;

grant execute on function public.submit_lead(text, text, text, text, text, text, date, text, text, text, text)
  to service_role;
grant execute on function public.claim_outbox(integer, uuid) to service_role;
grant execute on function public.finish_outbox(uuid, boolean, text) to service_role;
