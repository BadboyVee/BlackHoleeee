/*
 * Profile photos. The browser resizes the picked image and uploads it straight
 * to Supabase Storage (the avatars bucket, which only lets people write in
 * their own folder); the server then saves its address on the profile, after
 * checking it points at that folder. See 20261013150000_avatars.sql.
 */

export const AVATAR_BUCKET = "avatars";
export const AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
/** What people may pick. The upload itself is resized well under the bucket's 2 MB limit. */
export const AVATAR_PICK_MAX_BYTES = 10 * 1024 * 1024;
/** The square the photo is resized to, in pixels. */
export const AVATAR_SIZE = 512;

/** Where a person's photo lives in the bucket: one file, replaced on every upload. */
export function avatarPath(userId: string): string {
  return `${userId}/avatar.webp`;
}

/** The public address for a stored photo, with a version so browsers fetch the new one. */
export function avatarPublicUrl(supabaseUrl: string, userId: string, version: number): string {
  return `${supabaseUrl.replace(/\/+$/, "")}/storage/v1/object/public/${AVATAR_BUCKET}/${avatarPath(userId)}?v=${version}`;
}

/** True when `url` is this person's photo in this project's bucket, and nothing else. */
export function isOwnAvatarUrl(url: string, supabaseUrl: string, userId: string): boolean {
  const prefix = `${supabaseUrl.replace(/\/+$/, "")}/storage/v1/object/public/${AVATAR_BUCKET}/${avatarPath(userId)}`;
  if (!url.startsWith(prefix)) return false;
  const rest = url.slice(prefix.length);
  return rest === "" || /^\?v=\d{1,16}$/.test(rest);
}

export function avatarTypeProblem(type: string, size: number): string | null {
  if (!(AVATAR_TYPES as readonly string[]).includes(type)) return "Pick a JPG, PNG or WebP image.";
  if (size > AVATAR_PICK_MAX_BYTES) return "That image is over 10 MB. Pick a smaller one.";
  return null;
}

