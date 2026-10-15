-- Milestone 4: profile photos.
--
-- A public bucket, so a photo loads from its address without signing in (the
-- admin, the creator app and emails show it). Each person writes only inside
-- a folder named after their user id, and only small images. The address is
-- saved on profiles.avatar_url by the profile screen.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', true, 2097152, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Reading through the API (needed to replace a file) is limited to your own
-- folder too. Anyone can still load a photo by its public address.
create policy "Avatars: read your own folder"
  on storage.objects for select to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);

create policy "Avatars: upload into your own folder"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);

create policy "Avatars: replace in your own folder"
  on storage.objects for update to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);

create policy "Avatars: delete from your own folder"
  on storage.objects for delete to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);

-- Photos are https addresses only (Google's, or this project's storage). The
-- sign-up trigger drops anything else instead of failing the sign-up.
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
    case when char_length(avatar) <= 2048 and avatar ~* '^https://[^[:space:]]+$' then avatar end
  );
  return new;
end;
$$;

revoke all on function private.handle_new_user() from public, anon, authenticated, service_role;

alter table public.profiles
  add constraint profiles_avatar_url_https check (avatar_url is null or avatar_url ~* '^https://[^[:space:]]+$') not valid;
