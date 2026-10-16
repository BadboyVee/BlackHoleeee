-- Milestone 4: profile photos.
--
-- A public bucket, so a photo loads from its address without signing in (the
-- admin, the creator app and emails show it). Each person has exactly one
-- file, <user id>/avatar.webp, replaced on every upload, and only small
-- images. The address is saved on profiles.avatar_url by the profile screen.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', true, 2097152, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Reading through the API (needed to replace a file) is limited to your own
-- photo too. Anyone can still load a photo by its public address.
create policy "Avatars: read your own photo"
  on storage.objects for select to authenticated
  using (bucket_id = 'avatars' and name = (select auth.uid())::text || '/avatar.webp');

create policy "Avatars: upload your own photo"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars' and name = (select auth.uid())::text || '/avatar.webp');

create policy "Avatars: replace your own photo"
  on storage.objects for update to authenticated
  using (bucket_id = 'avatars' and name = (select auth.uid())::text || '/avatar.webp')
  with check (bucket_id = 'avatars' and name = (select auth.uid())::text || '/avatar.webp');

create policy "Avatars: delete your own photo"
  on storage.objects for delete to authenticated
  using (bucket_id = 'avatars' and name = (select auth.uid())::text || '/avatar.webp');

-- A photo is either the person's own file in this bucket or the Google profile
-- picture they signed up with, so nobody can make staff browsers load an image
-- from a server they control. The project's own address isn't known here, so
-- any *.supabase.co project is accepted for the bucket path (a local
-- `supabase start` on http won't pass; use the hosted project). The sign-up
-- trigger drops anything else instead of failing the sign-up.
create function private.is_known_avatar(p_url text, p_profile uuid)
returns boolean
language sql
immutable
set search_path = ''
as $$
  select p_url ~ '^https://lh[0-9]+\.googleusercontent\.com/[^[:space:]]+$'
    or p_url ~ ('^https://[a-z0-9]+\.supabase\.co/storage/v1/object/public/avatars/'
                || p_profile::text || '/avatar\.webp(\?v=[0-9]{1,16})?$')
$$;

revoke all on function private.is_known_avatar(text, uuid) from public, anon, authenticated, service_role;
-- The check constraint calls it, so the roles that write avatar_url need it.
grant execute on function private.is_known_avatar(text, uuid) to authenticated, service_role;

create or replace function private.handle_new_user()
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
    case when private.is_known_avatar(avatar, new.id) then avatar end
  );
  return new;
end;
$$;

revoke all on function private.handle_new_user() from public, anon, authenticated, service_role;

-- Photos from before this rule that don't follow it are dropped, so the rule holds for every row.
update public.profiles p set avatar_url = null
where p.avatar_url is not null and not private.is_known_avatar(p.avatar_url, p.id);

alter table public.profiles
  add constraint profiles_avatar_url_known check (avatar_url is null or private.is_known_avatar(avatar_url, id));
