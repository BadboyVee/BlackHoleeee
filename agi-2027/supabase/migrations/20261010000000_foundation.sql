-- Foundation: roles, profiles, and the helpers every later policy relies on.
--
-- Rules every migration in this project follows:
--   * RLS is on for every table, and every policy names the roles it applies to.
--   * New tables start with no privileges for anon or authenticated. Each grant
--     is written out, down to the column where it matters.
--   * Anything that changes more than one row or moves a status runs in a
--     SECURITY DEFINER function that checks the caller first, with an empty
--     search_path and fully qualified names.
--   * Helpers that policies call live in the `private` schema, which the API
--     never exposes.

create schema if not exists private;
revoke all on schema private from public;
grant usage on schema private to authenticated, service_role;

-- Roles and account states -----------------------------------------------------

create type public.user_role as enum ('admin', 'team', 'creator', 'applicant');
create type public.account_status as enum ('active', 'suspended', 'removed');

-- Shared trigger: keep updated_at current -----------------------------------------

create function private.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- Profiles ------------------------------------------------------------------------

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  role public.user_role not null default 'applicant',
  status public.account_status not null default 'active',
  email text,
  display_name text not null default '' check (char_length(display_name) <= 80),
  avatar_url text check (char_length(avatar_url) <= 2048),
  timezone text not null default 'UTC' check (char_length(timezone) between 1 and 64),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.profiles is
  'One row per signed-up user. Role and status change only through admin database functions.';

create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function private.touch_updated_at();

-- Who is calling? ----------------------------------------------------------------
-- SECURITY DEFINER so policies on profiles can call them without recursing into
-- profiles' own RLS. A suspended or removed account has no role at all.

create function private.current_user_role()
returns public.user_role
language sql
stable
security definer
set search_path = ''
as $$
  select p.role
  from public.profiles p
  where p.id = (select auth.uid()) and p.status = 'active'
$$;

create function private.is_staff()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(private.current_user_role() in ('admin', 'team'), false)
$$;

create function private.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(private.current_user_role() = 'admin', false)
$$;

-- Every new auth user gets a profile, starting as an applicant. --------------------

create function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  name text := coalesce(
    nullif(trim(new.raw_user_meta_data ->> 'full_name'), ''),
    nullif(trim(new.raw_user_meta_data ->> 'name'), ''),
    ''
  );
  avatar text := nullif(new.raw_user_meta_data ->> 'avatar_url', '');
begin
  insert into public.profiles (id, email, display_name, avatar_url)
  values (
    new.id,
    new.email,
    left(name, 80),
    case when char_length(avatar) <= 2048 then avatar end
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function private.handle_new_user();

-- Keep the email copy in sync when someone changes their address. ----------------

create function private.handle_user_email_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.profiles set email = new.email where id = new.id;
  return new;
end;
$$;

create trigger on_auth_user_email_changed
  after update of email on auth.users
  for each row
  when (old.email is distinct from new.email)
  execute function private.handle_user_email_change();

revoke all on all functions in schema private from public;
grant execute on function private.current_user_role() to authenticated, service_role;
grant execute on function private.is_staff() to authenticated, service_role;
grant execute on function private.is_admin() to authenticated, service_role;

-- Profile access -------------------------------------------------------------------

alter table public.profiles enable row level security;

revoke all on table public.profiles from anon, authenticated;
grant select on table public.profiles to authenticated;
-- Only these columns are user-editable. Role, status and email never are.
grant update (display_name, avatar_url, timezone) on table public.profiles to authenticated;

create policy "Users read their own profile"
  on public.profiles for select to authenticated
  using (id = (select auth.uid()));

create policy "Staff read every profile"
  on public.profiles for select to authenticated
  using ((select private.is_staff()));

create policy "Users update their own profile"
  on public.profiles for update to authenticated
  using (id = (select auth.uid()))
  with check (id = (select auth.uid()));

-- Health check ----------------------------------------------------------------------
-- Lets a deployment confirm it can reach the database, and which migration it's on.

create function public.health()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  latest text;
begin
  if to_regclass('supabase_migrations.schema_migrations') is not null then
    execute 'select max(version) from supabase_migrations.schema_migrations' into latest;
  end if;
  return jsonb_build_object(
    'ok', true,
    'db_time', now(),
    'schema_version', coalesce(latest, 'unknown')
  );
end;
$$;

revoke all on function public.health() from public;
grant execute on function public.health() to anon, authenticated, service_role;
