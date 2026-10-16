import type { Client } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { asAnon, asUser, connect, createUser } from "./helpers";

/*
 * Milestone 4: profile photos (supabase/migrations/20261013150000_avatars.sql).
 * The storage tables here are the test stand-in from supabase-shim.sql, with
 * row level security on, as in a real project.
 */

const RLS_VIOLATION = "42501";
const CHECK_VIOLATION = "23514";

let db: Client;
let amara: string;
let bayo: string;

beforeAll(async () => {
  db = await connect();
  amara = await createUser(db);
  bayo = await createUser(db);
});

afterAll(async () => {
  await db.end();
});

async function upload(name: string) {
  return db.query("insert into storage.objects (bucket_id, name, owner) values ('avatars', $1, auth.uid()) returning id", [name]);
}

async function attempt(fn: () => Promise<unknown>): Promise<string | null> {
  await db.query("savepoint attempt");
  try {
    await fn();
    return null;
  } catch (error) {
    return (error as { code?: string }).code ?? "unknown";
  } finally {
    await db.query("rollback to savepoint attempt");
  }
}

describe("the avatars bucket", () => {
  it("is public, small and images only", async () => {
    const { rows } = await db.query("select public, file_size_limit, allowed_mime_types from storage.buckets where id = 'avatars'");
    expect(rows).toEqual([{ public: true, file_size_limit: "2097152", allowed_mime_types: ["image/jpeg", "image/png", "image/webp"] }]);
  });

  it("lets people upload, replace, read and delete their own photo, and only that one file", async () => {
    await asUser(db, amara, async () => {
      expect(await attempt(() => upload(`${amara}/avatar.webp`))).toBeNull();
      expect(await attempt(() => upload(`${bayo}/avatar.webp`))).toBe(RLS_VIOLATION);
      expect(await attempt(() => upload("avatar.webp"))).toBe(RLS_VIOLATION);
      // Nothing else in their folder, so the bucket can't be used as free image hosting.
      expect(await attempt(() => upload(`${amara}/other.png`))).toBe(RLS_VIOLATION);
      expect(await attempt(() => upload(`${amara}/sub/avatar.webp`))).toBe(RLS_VIOLATION);

      await upload(`${amara}/avatar.webp`);
      const own = await db.query("update storage.objects set updated_at = now() where name = $1 returning id", [`${amara}/avatar.webp`]);
      expect(own.rowCount).toBe(1);
      const read = await db.query("select name from storage.objects where bucket_id = 'avatars'");
      expect(read.rows).toEqual([{ name: `${amara}/avatar.webp` }]);
      const removed = await db.query("delete from storage.objects where name = $1", [`${amara}/avatar.webp`]);
      expect(removed.rowCount).toBe(1);
    });
  });

  it("hides and protects other people's files", async () => {
    await db.query("insert into storage.objects (bucket_id, name, owner) values ('avatars', $1, $2)", [`${bayo}/avatar.webp`, bayo]);
    try {
      await asUser(db, amara, async () => {
        expect((await db.query("select 1 from storage.objects")).rowCount).toBe(0);
        expect((await db.query("update storage.objects set updated_at = now()")).rowCount).toBe(0);
        expect((await db.query("delete from storage.objects")).rowCount).toBe(0);
        // Moving a file into your own folder doesn't work either: the policy checks where it was.
        expect((await db.query("update storage.objects set name = $1", [`${amara}/stolen.webp`])).rowCount).toBe(0);
      });
      await asAnon(db, async () => {
        expect((await db.query("select 1 from storage.objects")).rowCount).toBe(0);
        expect(await attempt(() => db.query("insert into storage.objects (bucket_id, name) values ('avatars', 'x/avatar.webp')"))).toBe(
          RLS_VIOLATION,
        );
      });
    } finally {
      await db.query("delete from storage.objects");
    }
  });

  it("leaves other buckets alone", async () => {
    await db.query("insert into storage.buckets (id, name) values ('other', 'other')");
    try {
      await asUser(db, amara, async () => {
        expect(
          await attempt(() => db.query("insert into storage.objects (bucket_id, name) values ('other', $1)", [`${amara}/a.png`])),
        ).toBe(RLS_VIOLATION);
      });
    } finally {
      await db.query("delete from storage.buckets where id = 'other'");
    }
  });
});

describe("profile photo addresses", () => {
  it("accepts only their own photo in the bucket, or a Google profile picture", async () => {
    await asUser(db, amara, async () => {
      for (const url of [
        `https://project.supabase.co/storage/v1/object/public/avatars/${amara}/avatar.webp?v=1`,
        `https://project.supabase.co/storage/v1/object/public/avatars/${amara}/avatar.webp`,
        "https://lh3.googleusercontent.com/a/ACg8ocK=s96-c",
      ]) {
        await db.query("update public.profiles set avatar_url = $1 where id = $2", [url, amara]);
      }
      for (const bad of [
        "http://tracker.example/pixel.gif",
        "javascript:alert(1)",
        "https://example.com/a b.png",
        // A server they control would learn who opened their application, and when.
        "https://attacker.example/p.png?u=me",
        `https://attacker.example/storage/v1/object/public/avatars/${amara}/avatar.webp`,
        `https://project.supabase.co/storage/v1/object/public/avatars/${bayo}/avatar.webp`,
        `https://project.supabase.co/storage/v1/object/public/avatars/${amara}/other.png`,
        "https://lh3.googleusercontent.com.attacker.example/a",
      ]) {
        expect(await attempt(() => db.query("update public.profiles set avatar_url = $1 where id = $2", [bad, amara]))).toBe(
          CHECK_VIOLATION,
        );
      }
      await db.query("update public.profiles set avatar_url = null where id = $1", [amara]);
    });
  });

  it("drops any other photo at sign-up instead of refusing the account", async () => {
    const plain = await createUser(db, { meta: { avatar_url: "https://example.com/me.png", full_name: "Plain" } });
    const google = await createUser(db, { meta: { avatar_url: "https://lh3.googleusercontent.com/a/me", full_name: "Goog" } });
    const { rows } = await db.query("select id, avatar_url from public.profiles where id = any($1) order by display_name", [
      [plain, google],
    ]);
    expect(rows).toEqual([
      { id: google, avatar_url: "https://lh3.googleusercontent.com/a/me" },
      { id: plain, avatar_url: null },
    ]);
  });
});
