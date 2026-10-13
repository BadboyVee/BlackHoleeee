-- Milestone 3: accounts and sign in.
--
-- Follows the rules at the top of 20261010000000_foundation.sql.
--
-- What's here:
--   * public.custom_access_token_hook: Supabase Auth calls it each time it
--     issues a token, and it adds the person's role as the user_role claim
--     ('none' for a suspended or removed account), so the site can route people
--     by role without asking the database on every page. Turn it on once in
--     the dashboard: Authentication > Hooks > Customize Access Token (JWT)
--     Claims > public.custom_access_token_hook. Until then the site looks the
--     role up instead, which is slower but just as correct.
--   * Explicit grants on profiles for the service key, which Milestone 1 left
--     to Supabase's defaults.
--   * public.hit_rate_limit: limits for sign in, sign up and the emails Auth
--     sends, counted per salted hash the site's server makes. Never a raw IP
--     or email address.
--   * private.make_first_admin: the one time setup step that makes the
--     owner's account the admin, run by hand in the SQL editor.

-- Role claim in every token ----------------------------------------------------------

create function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_claims jsonb := coalesce(event -> 'claims', '{}'::jsonb);
  v_role public.user_role;
  v_status public.account_status;
begin
  select p.role, p.status into v_role, v_status
  from public.profiles p
  where p.id = (event ->> 'user_id')::uuid;

  -- Same rule as private.current_user_role(): an account that isn't active has no role.
  v_claims := pg_catalog.jsonb_set(
    v_claims,
    '{user_role}',
    pg_catalog.to_jsonb(case when v_status = 'active' then v_role::text else 'none' end)
  );
  return pg_catalog.jsonb_set(event, '{claims}', v_claims);
end;
$$;

comment on function public.custom_access_token_hook(jsonb) is
  'Supabase Auth hook: adds user_role (admin, team, creator, applicant, or none when the '
  'account is suspended, removed or has no profile) to every access token. Only Supabase '
  'Auth runs it. Enable it under Authentication > Hooks.';

revoke all on function public.custom_access_token_hook(jsonb) from public, anon, authenticated, service_role;
grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;

-- Profiles: explicit grants for the service key ------------------------------------------
-- Milestone 1 revoked everything from anon and authenticated but left the service
-- key on Supabase's defaults. It only ever needs to read profiles (for emails and,
-- later, admin work); role and status change only through database functions.

revoke all on table public.profiles from service_role;
grant select on table public.profiles to service_role;

-- Rate limits for sign in, sign up and Auth emails ------------------------------------
-- The limits live here, not in the site's code, so a server bug can't loosen them.
-- Windows are clock hours in UTC (see private.take_rate_limit).

create function public.hit_rate_limit(p_kind text, p_key text)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_limit integer;
begin
  case p_kind
    when 'sign_in_ip' then v_limit := 30;          -- per connection
    when 'sign_in_email' then v_limit := 10;       -- per account, so nobody can keep guessing one password
    when 'sign_up_ip' then v_limit := 10;          -- per connection
    when 'auth_email_ip' then v_limit := 10;       -- reset and confirmation emails, per connection
    when 'auth_email_address' then v_limit := 3;   -- per inbox, so nobody can flood someone with emails
    else
      raise exception 'Unknown rate limit kind: %', p_kind using errcode = '22023';
  end case;

  if p_key is null or btrim(p_key) = '' or char_length(p_key) > 128 then
    raise exception 'hit_rate_limit needs a key of 1 to 128 characters' using errcode = '22023';
  end if;

  return private.take_rate_limit(p_kind || ':' || p_key, v_limit, interval '1 hour');
end;
$$;

comment on function public.hit_rate_limit(text, text) is
  'Counts one hit for p_kind (sign_in_ip, sign_in_email, sign_up_ip, auth_email_ip or '
  'auth_email_address) and p_key (a salted hash from the server, never a raw IP or email). '
  'Returns false once the hour''s limit for that kind is used up. Service key only.';

revoke all on function public.hit_rate_limit(text, text) from public, anon, authenticated, service_role;
grant execute on function public.hit_rate_limit(text, text) to service_role;

-- The first admin ------------------------------------------------------------------------
-- Run once by hand in the Supabase SQL editor, after signing up on the site:
--   select private.make_first_admin('you@example.com');
-- It works only while there is no admin, so it can't be used to add a second one.
-- Team members join by invite from the admin (Milestone 9).

create function private.make_first_admin(p_email text)
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_user_id uuid;
  v_matches integer;
begin
  -- One run at a time, so two runs can't both see that there is no admin yet.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('agi-2027:make_first_admin'));

  if exists (select 1 from public.profiles p where p.role = 'admin') then
    raise exception 'There is already an admin. Add more people from the admin once team invites arrive.';
  end if;

  select count(*), min(u.id::text)::uuid into v_matches, v_user_id
  from auth.users u
  where lower(u.email) = lower(btrim(p_email));

  if v_matches = 0 then
    raise exception 'No account uses %. Sign up on the site first, then run this again.', p_email;
  elsif v_matches > 1 then
    raise exception 'More than one account uses %. Ask for help before going on.', p_email;
  end if;

  update public.profiles p
  set role = 'admin', status = 'active'
  where p.id = v_user_id;
  if not found then
    raise exception 'The account for % has no profile. Ask for help before going on.', p_email;
  end if;

  perform private.log_activity(
    null,
    'profile.role_changed',
    'profile',
    v_user_id::text,
    pg_catalog.jsonb_build_object('role', 'admin', 'via', 'make_first_admin')
  );

  return v_user_id;
end;
$$;

comment on function private.make_first_admin(text) is
  'One time setup: makes the account with this email the admin, only while there is no '
  'admin yet. Run it by hand in the SQL editor. Not reachable through the API.';

revoke all on function private.make_first_admin(text) from public, anon, authenticated, service_role;
