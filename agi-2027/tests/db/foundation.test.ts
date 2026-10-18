import type { Client } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { asAnon, asUser, connect, createUser, PERMISSION_DENIED, setProfile } from "./helpers";

let db: Client;

beforeAll(async () => {
  db = await connect();
});

afterAll(async () => {
  await db.end();
});

describe("new users", () => {
  it("get a profile as an applicant, named from their sign-up details", async () => {
    const id = await createUser(db, {
      email: "ada@example.com",
      meta: { full_name: "  Ada Lovelace ", avatar_url: "https://lh3.googleusercontent.com/a/ada" },
    });
    const { rows } = await db.query("select * from public.profiles where id = $1", [id]);
    expect(rows[0]).toMatchObject({
      role: "applicant",
      status: "active",
      email: "ada@example.com",
      display_name: "Ada Lovelace",
      avatar_url: "https://lh3.googleusercontent.com/a/ada",
      timezone: "UTC",
    });
  });

  it("still sign up when their name is long or missing", async () => {
    const longName = await createUser(db, { meta: { name: "x".repeat(200) } });
    const noName = await createUser(db);
    const { rows } = await db.query(
      "select id, display_name from public.profiles where id = any($1)",
      [[longName, noName]],
    );
    const byId = Object.fromEntries(rows.map((row) => [row.id, row.display_name]));
    expect(byId[longName]).toHaveLength(80);
    expect(byId[noName]).toBe("");
  });

  it("keep their profile email in sync when they change it", async () => {
    const id = await createUser(db, { email: "old@example.com" });
    await db.query("update auth.users set email = 'new@example.com' where id = $1", [id]);
    const { rows } = await db.query("select email from public.profiles where id = $1", [id]);
    expect(rows[0].email).toBe("new@example.com");
  });
});

describe("profile privacy", () => {
  it("lets a user read only their own profile", async () => {
    const me = await createUser(db);
    await createUser(db);
    const rows = await asUser(db, me, async () => {
      const result = await db.query("select id from public.profiles");
      return result.rows;
    });
    expect(rows).toEqual([{ id: me }]);
  });

  it("lets staff read every profile", async () => {
    const staff = await createUser(db);
    await setProfile(db, staff, { role: "team" });
    const [{ count: total }] = (await db.query("select count(*)::int as count from public.profiles")).rows;
    const visible = await asUser(db, staff, async () => {
      const result = await db.query("select count(*)::int as count from public.profiles");
      return result.rows[0].count;
    });
    expect(visible).toBe(total);
    expect(total).toBeGreaterThan(1);
  });

  it("drops staff access the moment a team member is suspended", async () => {
    const staff = await createUser(db);
    await setProfile(db, staff, { role: "team", status: "suspended" });
    const visible = await asUser(db, staff, async () => {
      const result = await db.query("select id from public.profiles");
      return result.rows;
    });
    expect(visible).toEqual([{ id: staff }]);
  });

  it("shows signed-out visitors nothing", async () => {
    await expect(
      asAnon(db, () => db.query("select id from public.profiles")),
    ).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });
});

describe("profile editing", () => {
  it("lets a user change their own name and time zone", async () => {
    const me = await createUser(db);
    const row = await asUser(db, me, async () => {
      const result = await db.query(
        "update public.profiles set display_name = 'New Name', timezone = 'Africa/Lagos' where id = $1 returning display_name, timezone, updated_at > created_at as touched",
        [me],
      );
      return result.rows[0];
    });
    expect(row).toEqual({ display_name: "New Name", timezone: "Africa/Lagos", touched: true });
  });

  it("never lets a user make themselves team or admin", async () => {
    const me = await createUser(db);
    for (const role of ["team", "admin"]) {
      await expect(
        asUser(db, me, () => db.query("update public.profiles set role = $2 where id = $1", [me, role])),
      ).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
    const { rows } = await db.query("select role from public.profiles where id = $1", [me]);
    expect(rows[0].role).toBe("applicant");
  });

  it("never lets a user lift their own suspension or change their email copy", async () => {
    const me = await createUser(db);
    await expect(
      asUser(db, me, () => db.query("update public.profiles set status = 'active' where id = $1", [me])),
    ).rejects.toMatchObject({ code: PERMISSION_DENIED });
    await expect(
      asUser(db, me, () =>
        db.query("update public.profiles set email = 'x@example.com' where id = $1", [me]),
      ),
    ).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });

  it("ignores attempts to edit someone else's profile", async () => {
    const me = await createUser(db);
    const other = await createUser(db, { meta: { full_name: "Other Person" } });
    const updated = await asUser(db, me, async () => {
      const result = await db.query("update public.profiles set display_name = 'Hacked' where id = $1", [other]);
      return result.rowCount;
    });
    expect(updated).toBe(0);
    const { rows } = await db.query("select display_name from public.profiles where id = $1", [other]);
    expect(rows[0].display_name).toBe("Other Person");
  });

  it("doesn't let users create or delete profiles directly", async () => {
    const me = await createUser(db);
    await expect(
      asUser(db, me, () =>
        db.query("insert into public.profiles (id) values (gen_random_uuid())"),
      ),
    ).rejects.toMatchObject({ code: PERMISSION_DENIED });
    await expect(
      asUser(db, me, () => db.query("delete from public.profiles where id = $1", [me])),
    ).rejects.toMatchObject({ code: PERMISSION_DENIED });
  });
});

describe("role helpers", () => {
  it("report the caller's role, and nothing once they're suspended", async () => {
    const admin = await createUser(db);
    await setProfile(db, admin, { role: "admin" });
    const asAdmin = await asUser(db, admin, async () => {
      const result = await db.query(
        "select private.current_user_role() as role, private.is_staff() as staff, private.is_admin() as admin",
      );
      return result.rows[0];
    });
    expect(asAdmin).toEqual({ role: "admin", staff: true, admin: true });

    await setProfile(db, admin, { status: "suspended" });
    const suspended = await asUser(db, admin, async () => {
      const result = await db.query("select private.is_staff() as staff, private.is_admin() as admin");
      return result.rows[0];
    });
    expect(suspended).toEqual({ staff: false, admin: false });
  });

  it("aren't callable by signed-out visitors", async () => {
    await expect(asAnon(db, () => db.query("select private.is_admin()"))).rejects.toMatchObject({
      code: PERMISSION_DENIED,
    });
  });
});

describe("health()", () => {
  it("answers for signed-out visitors so deployments can check the connection", async () => {
    const health = await asAnon(db, async () => {
      const result = await db.query("select public.health() as health");
      return result.rows[0].health;
    });
    expect(health).toMatchObject({ ok: true, schema_version: "unknown" });
    expect(Number.isNaN(Date.parse(health.db_time))).toBe(false);
  });
});
