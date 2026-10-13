import { randomUUID } from "node:crypto";

import type { Client } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { asAnon, asAuthAdmin, asService, asUser, connect, createUser, PERMISSION_DENIED, setProfile } from "./helpers";

/*
 * Milestone 3: accounts and sign in (supabase/migrations/20261013120000_accounts.sql).
 */

const INVALID_PARAMETER = "22023";

let db: Client;
const users: Record<"admin" | "team" | "creator" | "applicant" | "suspended" | "removed", string> = {
  admin: "",
  team: "",
  creator: "",
  applicant: "",
  suspended: "",
  removed: "",
};

/** The event Supabase Auth hands the hook when it issues a token. */
function tokenEvent(userId: string) {
  return {
    user_id: userId,
    claims: { sub: userId, aud: "authenticated", role: "authenticated", email: "someone@example.com" },
    authentication_method: "password",
  };
}

async function runHook(userId: string) {
  return asAuthAdmin(db, async () => {
    const { rows } = await db.query<{ result: { user_id: string; claims: Record<string, unknown> } }>(
      "select public.custom_access_token_hook($1::jsonb) as result",
      [JSON.stringify(tokenEvent(userId))],
    );
    return rows[0].result;
  });
}

/** Runs fn as the database owner (as the SQL editor does) and undoes everything afterwards. */
async function asOwnerRolledBack<T>(fn: () => Promise<T>) {
  await db.query("begin");
  try {
    return await fn();
  } finally {
    await db.query("rollback");
  }
}

beforeAll(async () => {
  db = await connect();
  users.admin = await createUser(db);
  await setProfile(db, users.admin, { role: "admin" });
  users.team = await createUser(db);
  await setProfile(db, users.team, { role: "team" });
  users.creator = await createUser(db);
  await setProfile(db, users.creator, { role: "creator" });
  users.applicant = await createUser(db);
  users.suspended = await createUser(db);
  await setProfile(db, users.suspended, { role: "creator", status: "suspended" });
  users.removed = await createUser(db);
  await setProfile(db, users.removed, { role: "team", status: "removed" });
});

afterAll(async () => {
  await db.end();
});

describe("the schema", () => {
  it("runs every new function as its owner with an empty search_path", async () => {
    const { rows } = await db.query(
      `select p.proname, p.prosecdef, p.proconfig
       from pg_proc p join pg_namespace n on n.oid = p.pronamespace
       where (n.nspname, p.proname) in (('public', 'custom_access_token_hook'),
         ('public', 'hit_rate_limit'), ('private', 'make_first_admin'))
       order by p.proname`,
    );
    expect(rows.map((row) => row.proname)).toEqual(["custom_access_token_hook", "hit_rate_limit", "make_first_admin"]);
    for (const row of rows) {
      expect(row.prosecdef, row.proname).toBe(true);
      expect(row.proconfig, row.proname).toEqual(['search_path=""']);
    }
  });
});

describe("custom_access_token_hook", () => {
  it("adds the role of an active account and keeps every other claim", async () => {
    for (const role of ["admin", "team", "creator", "applicant"] as const) {
      const result = await runHook(users[role]);
      expect(result.user_id, role).toBe(users[role]);
      expect(result.claims, role).toEqual({ ...tokenEvent(users[role]).claims, user_role: role });
    }
  });

  it("says none for a suspended or removed account, and for a user with no profile", async () => {
    expect((await runHook(users.suspended)).claims.user_role).toBe("none");
    expect((await runHook(users.removed)).claims.user_role).toBe("none");
    expect((await runHook(randomUUID())).claims.user_role).toBe("none");
  });

  it("follows role changes the next time a token is issued", async () => {
    const userId = await createUser(db);
    expect((await runHook(userId)).claims.user_role).toBe("applicant");
    await setProfile(db, userId, { role: "creator" });
    expect((await runHook(userId)).claims.user_role).toBe("creator");
  });

  it("runs only for Supabase Auth, never through the API", async () => {
    const sql = `select public.custom_access_token_hook('${JSON.stringify(tokenEvent(users.admin))}'::jsonb)`;
    await expect(asAnon(db, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
    for (const who of ["applicant", "creator", "team", "admin"] as const) {
      await expect(asUser(db, users[who], () => db.query(sql)), who).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
    await expect(asService(db, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });
});

describe("profiles and the service key", () => {
  it("lets the service key read every profile", async () => {
    const count = await asService(db, async () => {
      const { rows } = await db.query<{ count: string }>("select count(*) from public.profiles");
      return Number(rows[0].count);
    });
    expect(count).toBeGreaterThanOrEqual(Object.keys(users).length);
  });

  it("never lets the service key change, add or delete a profile", async () => {
    const writes = [
      `update public.profiles set role = 'admin' where id = '${users.applicant}'`,
      `update public.profiles set display_name = 'x' where id = '${users.applicant}'`,
      `insert into public.profiles (id) values ('${randomUUID()}')`,
      `delete from public.profiles where id = '${users.applicant}'`,
    ];
    for (const sql of writes) {
      await expect(asService(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
  });
});

describe("hit_rate_limit", () => {
  const limits = {
    sign_in_ip: 30,
    sign_in_email: 10,
    sign_up_ip: 10,
    auth_email_ip: 10,
    auth_email_address: 3,
  } as const;

  async function hits(kind: string, key: string, times: number) {
    const results: boolean[] = [];
    for (let i = 0; i < times; i += 1) {
      const { rows } = await db.query<{ ok: boolean }>("select public.hit_rate_limit($1, $2) as ok", [kind, key]);
      results.push(rows[0].ok);
    }
    return results;
  }

  it("allows each kind's hourly limit per key, then refuses", async () => {
    await asService(db, async () => {
      for (const [kind, limit] of Object.entries(limits)) {
        const results = await hits(kind, randomUUID(), limit + 2);
        expect(results.slice(0, limit).every(Boolean), kind).toBe(true);
        expect(results.slice(limit), kind).toEqual([false, false]);
      }
    });
  });

  it("counts each key and each kind on its own", async () => {
    await asService(db, async () => {
      const key = randomUUID();
      expect(await hits("auth_email_address", key, 4)).toEqual([true, true, true, false]);
      // The same key under another kind, and another key under the same kind, start fresh.
      expect(await hits("auth_email_ip", key, 1)).toEqual([true]);
      expect(await hits("auth_email_address", randomUUID(), 1)).toEqual([true]);
    });
  });

  it("stores the kind and the key the server sent, nothing more", async () => {
    await asService(db, async () => {
      const key = randomUUID();
      await hits("sign_in_email", key, 1);
      await db.query("reset role");
      const { rows } = await db.query("select bucket, hits from public.rate_limits where bucket like $1", [`%${key}`]);
      expect(rows).toEqual([{ bucket: `sign_in_email:${key}`, hits: 1 }]);
    });
  });

  it("refuses unknown kinds and empty or overlong keys", async () => {
    for (const [kind, key] of [
      ["lead", "key"],
      ["", "key"],
      ["sign_in_ip", ""],
      ["sign_in_ip", "   "],
      ["sign_in_ip", "k".repeat(129)],
    ]) {
      await expect(
        asService(db, () => db.query("select public.hit_rate_limit($1, $2)", [kind, key])),
        `${kind}/${key.slice(0, 5)}`,
      ).rejects.toMatchObject({ code: INVALID_PARAMETER });
    }
    await expect(asService(db, () => db.query("select public.hit_rate_limit('sign_in_ip', null)"))).rejects.toMatchObject({
      code: INVALID_PARAMETER,
    });
  });

  it("is for the service key only", async () => {
    const sql = "select public.hit_rate_limit('sign_in_ip', 'key')";
    await expect(asAnon(db, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
    await expect(asUser(db, users.admin, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });
});

describe("make_first_admin", () => {
  /** Inside asOwnerRolledBack: no admins at all, as on a fresh project. */
  async function withoutAdmins() {
    await db.query("update public.profiles set role = 'team' where role = 'admin'");
  }

  async function profileOf(userId: string) {
    const { rows } = await db.query("select role, status from public.profiles where id = $1", [userId]);
    return rows[0];
  }

  it("makes the account with that email the admin, whatever the letter case, and logs it", async () => {
    const email = `Owner.${randomUUID()}@Example.com`;
    const owner = await createUser(db, { email });
    await asOwnerRolledBack(async () => {
      await withoutAdmins();
      const { rows } = await db.query("select private.make_first_admin($1) as id", [`  ${email.toLowerCase()} `]);
      expect(rows[0].id).toBe(owner);
      expect(await profileOf(owner)).toEqual({ role: "admin", status: "active" });

      const log = await db.query(
        "select actor, action, entity_type, details from public.activity_log where entity_id = $1",
        [owner],
      );
      expect(log.rows).toEqual([
        {
          actor: null,
          action: "profile.role_changed",
          entity_type: "profile",
          details: { role: "admin", via: "make_first_admin" },
        },
      ]);
    });
  });

  it("refuses once there is an admin, so it can never add a second one", async () => {
    const email = `second.${randomUUID()}@example.com`;
    const someone = await createUser(db, { email });
    await asOwnerRolledBack(async () => {
      await expect(db.query("select private.make_first_admin($1)", [email])).rejects.toThrow(/already an admin/);
    });
    expect(await profileOf(someone)).toEqual({ role: "applicant", status: "active" });
  });

  it("refuses an email nobody signed up with", async () => {
    await asOwnerRolledBack(async () => {
      await withoutAdmins();
      await expect(db.query("select private.make_first_admin($1)", ["nobody@example.com"])).rejects.toThrow(
        /Sign up on the site first/,
      );
    });
  });

  it("can't be called through the API, not even with the service key", async () => {
    const sql = "select private.make_first_admin('someone@example.com')";
    await expect(asAnon(db, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
    for (const who of ["applicant", "creator", "team", "admin"] as const) {
      await expect(asUser(db, users[who], () => db.query(sql)), who).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
    await expect(asService(db, () => db.query(sql))).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });
});
