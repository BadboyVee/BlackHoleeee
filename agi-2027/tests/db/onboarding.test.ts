import { randomUUID } from "node:crypto";

import type { Client } from "pg";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { connect, createUser, PERMISSION_DENIED, setProfile } from "./helpers";

/*
 * Milestone 4: creator onboarding
 * (supabase/migrations/20261013140000_creator_onboarding.sql).
 *
 * Each scenario runs in one transaction that's rolled back at the end, and
 * switches between callers inside it, exactly as requests through the API
 * would arrive: the authenticated role with the user's id in the JWT claims.
 */

const CHECK_VIOLATION = "23514";
const UNIQUE_VIOLATION = "23505";
const INVALID_PARAMETER = "22023";
const CONFLICT = "P0409";
const INVITE_UNUSABLE = "P0410";

const EVM = "0x52908400098527886E0F7030069857D2E4169EE7";
const SOLANA = "7EYnhQoR9YM3N7UoaKRoA44Uy8JeaZV3qyouov87awMs";
const TRON = "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy";

let db: Client;

type Caller = string | "anon" | "owner";

/** Runs a scenario in one transaction, rolled back at the end. `as` switches the caller. */
async function scenario(fn: (as: (who: Caller) => Promise<void>) => Promise<void>) {
  await db.query("begin");
  try {
    await fn(async (who) => {
      await db.query("reset role");
      if (who === "owner") return;
      if (who === "anon") {
        await db.query("set local role anon");
        await db.query("select set_config('request.jwt.claims', $1, true)", [JSON.stringify({ role: "anon" })]);
        return;
      }
      await db.query("set local role authenticated");
      await db.query("select set_config('request.jwt.claims', $1, true)", [
        JSON.stringify({ sub: who, role: "authenticated" }),
      ]);
    });
  } finally {
    await db.query("rollback");
  }
}

/** Expects a statement to fail with `code`, without aborting the scenario's transaction. */
async function fails(sql: string, params: unknown[], code: string, message?: RegExp) {
  await db.query("savepoint attempt");
  try {
    await db.query(sql, params);
    throw new Error(`Expected ${code} from: ${sql}`);
  } catch (error) {
    const caught = error as { code?: string; message: string };
    if (caught.message.startsWith("Expected ")) throw error;
    expect(caught.code, `${sql}: ${caught.message}`).toBe(code);
    if (message) expect(caught.message).toMatch(message);
  } finally {
    await db.query("rollback to savepoint attempt");
  }
}

async function one<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T> {
  const { rows } = await db.query(sql, params);
  return rows[0] as T;
}

async function rows<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T[]> {
  return (await db.query(sql, params)).rows as T[];
}

const answers = {
  display_name: "Amara Okafor",
  x_handle: "amarabuilds",
  tiktok: null as string | null,
  youtube: "https://youtube.com/@amara",
  instagram: null as string | null,
  linkedin: null as string | null,
  niches: ["ai", "startups"],
  followers: 18400,
  avg_views: 6200,
  country: "ng",
  best_posts: [
    "https://x.com/amarabuilds/status/1",
    "https://x.com/amarabuilds/status/2",
    "https://x.com/amarabuilds/status/3",
  ],
  why: "I review AI tools every week for founders who build in public.",
  referral: null as string | null,
};

function apply(values: Partial<typeof answers> = {}) {
  const v = { ...answers, ...values };
  return db.query<{ application_id: string; outbox_id: string }>(
    `select * from public.submit_application(
       p_display_name => $1, p_x_handle => $2, p_tiktok_url => $3, p_youtube_url => $4,
       p_instagram_url => $5, p_linkedin_url => $6, p_niches => $7, p_followers => $8,
       p_avg_views => $9, p_country => $10, p_best_posts => $11, p_why => $12, p_referral_code => $13)`,
    [v.display_name, v.x_handle, v.tiktok, v.youtube, v.instagram, v.linkedin, v.niches, v.followers, v.avg_views, v.country, v.best_posts, v.why, v.referral],
  );
}

const APPLY_SQL = "select * from public.submit_application('A', 'handle_x', null, null, null, null, '{}', 1, 1, 'NG', array['https://x.com/a/status/1'], 'Twenty characters at least.', null)";

let admin: string;
let team: string;
let creator: string;
let creatorEmail: string;

beforeAll(async () => {
  db = await connect();
  admin = await createUser(db);
  await setProfile(db, admin, { role: "admin" });
  team = await createUser(db);
  await setProfile(db, team, { role: "team" });
  creatorEmail = `creator.${randomUUID()}@example.com`;
  creator = await createUser(db, { email: creatorEmail });
  await setProfile(db, creator, { role: "creator" });
});

afterAll(async () => {
  await db.end();
});

describe("the schema", () => {
  it("has row level security on every new table", async () => {
    const result = await rows(
      `select relname, relrowsecurity from pg_class
       where oid in ('public.applications'::regclass, 'public.application_reviews'::regclass,
                     'public.invites'::regclass, 'public.payout_details'::regclass)
       order by relname`,
    );
    expect(result).toEqual([
      { relname: "application_reviews", relrowsecurity: true },
      { relname: "applications", relrowsecurity: true },
      { relname: "invites", relrowsecurity: true },
      { relname: "payout_details", relrowsecurity: true },
    ]);
  });

  it("runs every function that changes data as its owner with an empty search_path", async () => {
    const result = await rows<{ proname: string; prosecdef: boolean; proconfig: string[] }>(
      `select p.proname, p.prosecdef, p.proconfig
       from pg_proc p join pg_namespace n on n.oid = p.pronamespace
       where (n.nspname, p.proname) in (('public', 'submit_application'), ('public', 'review_application'),
         ('public', 'create_invite'), ('public', 'revoke_invite'), ('public', 'invite_preview'),
         ('public', 'redeem_invite'), ('public', 'set_payout_details'), ('public', 'my_referrals'),
         ('private', 'assign_referral_code'), ('private', 'queue_profile_email'), ('private', 'approve_profile'))`,
    );
    expect(result).toHaveLength(11);
    for (const row of result) {
      expect(row.prosecdef, row.proname).toBe(true);
      expect(row.proconfig, row.proname).toEqual(['search_path=""']);
    }
  });

  it("keeps the private helpers away from every API caller", async () => {
    const helpers = [
      "select private.assign_referral_code(gen_random_uuid())",
      "select private.queue_profile_email(gen_random_uuid(), 'x', '{}'::jsonb)",
      "select private.approve_profile(gen_random_uuid(), null, 'x')",
      "select private.random_code(8)",
    ];
    await scenario(async (as) => {
      for (const who of ["anon", admin, creator]) {
        await as(who);
        for (const sql of helpers) await fails(sql, [], PERMISSION_DENIED);
      }
    });
  });
});

describe("profiles", () => {
  it("lets creators edit their own profile, within its limits", async () => {
    await scenario(async (as) => {
      await as(creator);
      await db.query(
        `update public.profiles set bio = 'Builder.', niches = '{ai,design}', followers = 12000, avg_views = 3000,
           country = 'GB', rate_per_post = 150, rate_currency = 'USDC', instagram_url = 'https://instagram.com/x'
         where id = $1`,
        [creator],
      );
      await as("owner");
      expect(await one("select bio, niches, rate_per_post from public.profiles where id = $1", [creator])).toEqual({
        bio: "Builder.",
        niches: ["ai", "design"],
        rate_per_post: "150.00",
      });

      await as(creator);
      for (const sql of [
        "update public.profiles set niches = '{knitting}' where id = $1",
        "update public.profiles set country = 'Nigeria' where id = $1",
        "update public.profiles set rate_per_post = 10, rate_currency = null where id = $1",
        "update public.profiles set instagram_url = 'http://instagram.com/x' where id = $1",
        "update public.profiles set niches = '{ai,tech,crypto,startups,design,gaming}' where id = $1",
        // Each social link points at its own platform, as the forms check.
        "update public.profiles set linkedin_url = 'https://evil.example/login' where id = $1",
        "update public.profiles set instagram_url = 'https://instagram.com.evil.example/x' where id = $1",
        "update public.profiles set tiktok_url = 'https://tiktok.com@evil.example/x' where id = $1",
        "update public.profiles set youtube_url = 'https://tiktok.com/@amara' where id = $1",
      ]) {
        await fails(sql, [creator], CHECK_VIOLATION);
      }
      await as(creator);
      await db.query(
        `update public.profiles set youtube_url = 'https://youtu.be/abc', tiktok_url = 'https://www.tiktok.com/@amara',
           linkedin_url = 'https://uk.linkedin.com/in/amara' where id = $1`,
        [creator],
      );
    });
  });

  it("keeps applicants' answers as sent, and stops suspended creators editing", async () => {
    const applicant = await createUser(db);
    const suspended = await createUser(db);
    await setProfile(db, suspended, { role: "creator", status: "suspended" });
    await scenario(async (as) => {
      await as(applicant);
      await fails("update public.profiles set followers = 2000000000 where id = $1", [applicant], PERMISSION_DENIED);
      await fails("update public.profiles set linkedin_url = 'https://linkedin.com/in/x' where id = $1", [applicant], PERMISSION_DENIED);
      // Their name is still theirs to change.
      await db.query("update public.profiles set display_name = 'New name' where id = $1", [applicant]);
      await as(suspended);
      await fails("update public.profiles set bio = 'Back.' where id = $1", [suspended], PERMISSION_DENIED);
    });
  });

  it("never lets creators change their X handle, role, referral code or referrer", async () => {
    await scenario(async (as) => {
      await as(creator);
      for (const sql of [
        "update public.profiles set x_handle = 'someone_else' where id = $1",
        "update public.profiles set role = 'admin' where id = $1",
        "update public.profiles set referral_code = 'aaaaaaaa' where id = $1",
        "update public.profiles set referred_by = null where id = $1",
      ]) {
        await fails(sql, [creator], PERMISSION_DENIED);
      }
    });
  });
});

describe("applying", () => {
  it("fills in the profile, saves the answers, emails the owner and logs it", async () => {
    const applicant = await createUser(db);
    await scenario(async (as) => {
      await as(applicant);
      const { rows: [result] } = await apply();
      expect(result.application_id).toMatch(/^[0-9a-f-]{36}$/);

      await as("owner");
      expect(
        await one(
          "select display_name, x_handle, youtube_url, tiktok_url, niches, followers, avg_views, country, role from public.profiles where id = $1",
          [applicant],
        ),
      ).toEqual({
        display_name: "Amara Okafor",
        x_handle: "amarabuilds",
        youtube_url: "https://youtube.com/@amara",
        tiktok_url: null,
        niches: ["ai", "startups"],
        followers: 18400,
        avg_views: 6200,
        country: "NG",
        role: "applicant",
      });
      expect(await one("select status, best_posts, why, referred_by from public.applications where id = $1", [result.application_id])).toEqual({
        status: "submitted",
        best_posts: answers.best_posts,
        why: answers.why,
        referred_by: null,
      });
      expect(await one("select recipient, template, payload from public.outbox where id = $1", [result.outbox_id])).toEqual({
        recipient: "owner",
        template: "application_received",
        payload: { application_id: result.application_id },
      });
      expect(await one("select actor, action from public.activity_log where entity_id = $1", [result.application_id])).toEqual({
        actor: applicant,
        action: "application.submitted",
      });
    });
  });

  it("takes one application per person", async () => {
    const applicant = await createUser(db);
    await scenario(async (as) => {
      await as(applicant);
      await apply();
      await fails(APPLY_SQL, [], CONFLICT, /already_applied/);
    });
  });

  it("is for applicants only", async () => {
    await scenario(async (as) => {
      await as("anon");
      await fails(APPLY_SQL, [], PERMISSION_DENIED);
      for (const who of [creator, team, admin]) {
        await as(who);
        await fails(APPLY_SQL, [], PERMISSION_DENIED);
      }
    });
  });

  it("refuses broken answers and a handle an approved creator has", async () => {
    const applicant = await createUser(db);
    const other = await createUser(db);
    await scenario(async (as) => {
      await as(applicant);
      const cases: [Partial<typeof answers>, string][] = [
        [{ best_posts: [] }, CHECK_VIOLATION],
        [{ best_posts: ["http://x.com/a/status/1"] }, CHECK_VIOLATION],
        [{ best_posts: ["https://x.com/a/status/1", null as unknown as string] }, CHECK_VIOLATION],
        [{ why: "Too short." }, CHECK_VIOLATION],
        [{ niches: ["ai", "knitting"] }, CHECK_VIOLATION],
        [{ x_handle: "not a handle" }, CHECK_VIOLATION],
        [{ country: "Nigeria" }, CHECK_VIOLATION],
      ];
      for (const [values, code] of cases) {
        await db.query("savepoint attempt");
        await expect(apply(values), JSON.stringify(values)).rejects.toMatchObject({ code });
        await db.query("rollback to savepoint attempt");
      }

      // Two applicants can claim the same handle: staff decide who's real.
      await as(other);
      await apply({ x_handle: "shared_handle" });
      await as(applicant);
      await db.query("savepoint attempt");
      await apply({ x_handle: "SHARED_handle" });
      await db.query("rollback to savepoint attempt");

      // A handle an approved account has is taken.
      await as("owner");
      await db.query("update public.profiles set role = 'creator' where id = $1", [other]);
      await as(applicant);
      await db.query("savepoint attempt");
      await expect(apply({ x_handle: "SHARED_handle" })).rejects.toMatchObject({ code: UNIQUE_VIOLATION });
      await db.query("rollback to savepoint attempt");
    });
  });

  it("notes the referrer only for an active creator's code, never the applicant's own", async () => {
    const referred = await createUser(db);
    const suspended = await createUser(db);
    await scenario(async (as) => {
      await as("owner");
      const code = await one<{ code: string }>("select private.assign_referral_code($1) as code", [creator]);
      await setProfile(db, suspended, { role: "creator", status: "suspended" });
      const suspendedCode = await one<{ code: string }>("select private.assign_referral_code($1) as code", [suspended]);

      await as(referred);
      const { rows: [result] } = await apply({ referral: ` ${code.code.toUpperCase()} `, x_handle: "referred_one" });
      await as("owner");
      expect(await one("select referred_by from public.applications where id = $1", [result.application_id])).toEqual({ referred_by: creator });
      expect(await one("select referred_by from public.profiles where id = $1", [referred])).toEqual({ referred_by: creator });

      // A suspended creator's code, or no such code, is simply ignored.
      const second = await createUser(db);
      await as(second);
      const { rows: [ignored] } = await apply({ referral: suspendedCode.code, x_handle: "second_one" });
      await as("owner");
      expect(await one("select referred_by from public.applications where id = $1", [ignored.application_id])).toEqual({ referred_by: null });
    });
  });
});

describe("reviewing applications", () => {
  async function submitted() {
    const applicant = await createUser(db, { email: `applicant.${randomUUID()}@example.com` });
    await db.query("begin");
    await db.query("set local role authenticated");
    await db.query("select set_config('request.jwt.claims', $1, true)", [JSON.stringify({ sub: applicant, role: "authenticated" })]);
    const { rows: [result] } = await apply({ x_handle: `h${randomUUID().slice(0, 8)}` });
    await db.query("commit");
    return { applicant, applicationId: result.application_id };
  }

  it("approves: the applicant becomes a creator with a referral code, and is emailed", async () => {
    const { applicant, applicationId } = await submitted();
    await scenario(async (as) => {
      await as(team);
      const outbox = await one<{ id: string }>("select public.review_application($1, 'approve', ' Strong AI audience. ') as id", [applicationId]);

      await as("owner");
      expect(await one("select status, reviewed_at is not null as reviewed from public.applications where id = $1", [applicationId])).toEqual({
        status: "approved",
        reviewed: true,
      });
      expect(await one("select reviewed_by, note from public.application_reviews where application_id = $1", [applicationId])).toEqual({
        reviewed_by: team,
        note: "Strong AI audience.",
      });
      const profile = await one<{ role: string; referral_code: string; email: string }>(
        "select role, referral_code, email from public.profiles where id = $1",
        [applicant],
      );
      expect(profile.role).toBe("creator");
      expect(profile.referral_code).toMatch(/^[a-f0-9]{8}$/);
      expect(await one("select recipient, template, payload from public.outbox where id = $1", [outbox.id])).toEqual({
        recipient: profile.email,
        template: "application_approved",
        payload: { application_id: applicationId, profile_id: applicant },
      });
      const log = await rows("select actor, action from public.activity_log where entity_id in ($1, $2) order by id", [applicationId, applicant]);
      expect(log).toEqual([
        { actor: applicant, action: "application.submitted" },
        { actor: team, action: "profile.role_changed" },
        { actor: team, action: "application.approved" },
      ]);
    });
  });

  it("rejects: the applicant stays an applicant and is emailed", async () => {
    const { applicant, applicationId } = await submitted();
    await scenario(async (as) => {
      await as(admin);
      const outbox = await one<{ id: string }>("select public.review_application($1, 'reject', 'Mostly giveaways.') as id", [applicationId]);
      await as("owner");
      expect(await one("select status from public.applications where id = $1", [applicationId])).toEqual({ status: "rejected" });
      expect(await one("select role, referral_code from public.profiles where id = $1", [applicant])).toEqual({ role: "applicant", referral_code: null });
      expect(await one("select template from public.outbox where id = $1", [outbox.id])).toEqual({ template: "application_rejected" });
    });
  });

  it("decides each application once, and only approve or reject", async () => {
    const { applicationId } = await submitted();
    await scenario(async (as) => {
      await as(admin);
      await fails("select public.review_application($1, 'maybe')", [applicationId], INVALID_PARAMETER);
      await db.query("select public.review_application($1, 'reject')", [applicationId]);
      await fails("select public.review_application($1, 'approve')", [applicationId], CONFLICT, /already_reviewed/);
      await fails("select public.review_application(gen_random_uuid(), 'approve')", [], "P0002");
    });
  });

  it("keeps the team's note and who decided away from the applicant", async () => {
    const { applicant, applicationId } = await submitted();
    await scenario(async (as) => {
      await as(team);
      await db.query("select public.review_application($1, 'reject', 'Mostly giveaways.')", [applicationId]);
      await as(applicant);
      expect(await rows("select id, status from public.applications")).toEqual([{ id: applicationId, status: "rejected" }]);
      expect(await rows("select note from public.application_reviews")).toEqual([]);
      await as(admin);
      expect(await rows("select note from public.application_reviews where application_id = $1", [applicationId])).toEqual([
        { note: "Mostly giveaways." },
      ]);
    });
  });

  it("won't approve a second account with a handle an approved creator has", async () => {
    const handle = `h${randomUUID().slice(0, 8)}`;
    const make = async () => {
      const applicant = await createUser(db);
      await db.query("begin");
      await db.query("set local role authenticated");
      await db.query("select set_config('request.jwt.claims', $1, true)", [JSON.stringify({ sub: applicant, role: "authenticated" })]);
      const { rows: [result] } = await apply({ x_handle: handle });
      await db.query("commit");
      return result.application_id as string;
    };
    const real = await make();
    const copycat = await make();
    await scenario(async (as) => {
      await as(team);
      await db.query("select public.review_application($1, 'approve')", [real]);
      await fails("select public.review_application($1, 'approve')", [copycat], UNIQUE_VIOLATION);
    });
  });

  it("is for staff only", async () => {
    const { applicant, applicationId } = await submitted();
    await scenario(async (as) => {
      for (const who of ["anon", applicant, creator]) {
        await as(who);
        await fails("select public.review_application($1, 'approve')", [applicationId], PERMISSION_DENIED);
      }
    });
  });

  it("shows applicants their own application, staff every one, and nobody else anything", async () => {
    const first = await submitted();
    const second = await submitted();
    await scenario(async (as) => {
      await as(first.applicant);
      expect(await rows("select id from public.applications")).toEqual([{ id: first.applicationId }]);
      await as(creator);
      expect(await rows("select id from public.applications")).toEqual([]);
      await as("anon");
      await fails("select id from public.applications", [], PERMISSION_DENIED);
      await as(team);
      const seen = (await rows<{ id: string }>("select id from public.applications")).map((row) => row.id);
      expect(seen).toEqual(expect.arrayContaining([first.applicationId, second.applicationId]));
      // Nobody writes to the table directly; the functions do.
      await fails("update public.applications set status = 'approved' where id = $1", [first.applicationId], PERMISSION_DENIED);
    });
  });
});

describe("invite links", () => {
  async function newInvite(values: { maxUses?: number | null; expiresIn?: string | null } = {}) {
    const invite = await one<{ id: string; code: string; uses: number }>(
      `select (i).id, (i).code, (i).uses from (
         select public.create_invite('Telegram group', $1, case when $2::text is null then null else now() + $2::interval end) as i
       ) created`,
      [values.maxUses ?? null, values.expiresIn ?? null],
    );
    return invite;
  }

  it("lets only the admin create, see and revoke them", async () => {
    await scenario(async (as) => {
      await as(admin);
      const invite = await newInvite({ maxUses: 25 });
      expect(invite.code).toMatch(/^[a-f0-9]{16}$/);
      expect(await rows("select label, max_uses, uses from public.invites where id = $1", [invite.id])).toEqual([
        { label: "Telegram group", max_uses: 25, uses: 0 },
      ]);

      await as(team);
      await fails("select public.create_invite()", [], PERMISSION_DENIED);
      expect(await rows("select id from public.invites")).toEqual([]);
      await fails("select public.revoke_invite($1)", [invite.id], PERMISSION_DENIED);

      await as(admin);
      await db.query("select public.revoke_invite($1)", [invite.id]);
      await as("owner");
      expect(await one("select revoked_at is not null as revoked from public.invites where id = $1", [invite.id])).toEqual({ revoked: true });
      expect(await one("select count(*)::int as n from public.activity_log where entity_id = $1", [invite.id])).toEqual({ n: 2 });
    });
  });

  it("refuses an expiry in the past", async () => {
    await scenario(async (as) => {
      await as(admin);
      await fails("select public.create_invite('x', null, now() - interval '1 minute')", [], INVALID_PARAMETER);
    });
  });

  it("tells anyone whether a code works, and nothing more", async () => {
    await scenario(async (as) => {
      await as(admin);
      const valid = await newInvite();
      const usedUp = await newInvite({ maxUses: 1 });
      const revoked = await newInvite();
      await db.query("select public.revoke_invite($1)", [revoked.id]);
      await as("owner");
      await db.query("update public.invites set uses = 1 where id = $1", [usedUp.id]);
      await db.query("update public.invites set expires_at = now() - interval '1 second' where id = $1", [valid.id]);
      const fresh = await one<{ code: string }>("select code from public.invites where id = $1", [valid.id]);

      await as("anon");
      const state = async (code: string) => (await one<{ s: string }>("select public.invite_preview($1) as s", [code])).s;
      expect(await state(fresh.code)).toBe("expired");
      expect(await state(usedUp.code)).toBe("used_up");
      expect(await state(revoked.code)).toBe("revoked");
      expect(await state("0000000000000000")).toBe("unknown");
      expect(await state("not even hex")).toBe("unknown");
    });
  });

  it("approves an applicant straight away, counting the use and sending a welcome", async () => {
    const newcomer = await createUser(db, { email: `newcomer.${randomUUID()}@example.com` });
    await scenario(async (as) => {
      await as(admin);
      const invite = await newInvite({ maxUses: 1 });

      await as(newcomer);
      expect(await one<{ s: string }>("select public.invite_preview($1) as s", [invite.code.toUpperCase()])).toEqual({ s: "valid" });
      const outbox = await one<{ id: string }>("select public.redeem_invite($1) as id", [` ${invite.code} `]);

      await as("owner");
      expect(await one("select uses from public.invites where id = $1", [invite.id])).toEqual({ uses: 1 });
      expect(await one("select role, referral_code is not null as has_code from public.profiles where id = $1", [newcomer])).toEqual({
        role: "creator",
        has_code: true,
      });
      expect(await one("select status, invite_id, best_posts, why from public.applications where applicant = $1", [newcomer])).toEqual({
        status: "approved",
        invite_id: invite.id,
        best_posts: null,
        why: null,
      });
      expect(await one("select template, payload from public.outbox where id = $1", [outbox.id])).toEqual({
        template: "application_approved",
        payload: { invite_id: invite.id, profile_id: newcomer },
      });

      // The single use is gone now.
      const late = await createUser(db);
      await as(late);
      await fails("select public.redeem_invite($1)", [invite.code], INVITE_UNUSABLE, /invite_used_up/);
    });
  });

  it("approves an application that's already waiting", async () => {
    const applicant = await createUser(db);
    await scenario(async (as) => {
      await as(applicant);
      await apply({ x_handle: "waiting_one" });
      await as(admin);
      const invite = await newInvite();
      await as(applicant);
      await db.query("select public.redeem_invite($1)", [invite.code]);
      await as("owner");
      expect(await one("select status, invite_id, why from public.applications where applicant = $1", [applicant])).toEqual({
        status: "approved",
        invite_id: invite.id,
        why: answers.why,
      });
    });
  });

  it("refuses revoked, expired and unknown codes, and anyone who isn't an applicant", async () => {
    const applicant = await createUser(db);
    await scenario(async (as) => {
      await as(admin);
      const revoked = await newInvite();
      await db.query("select public.revoke_invite($1)", [revoked.id]);
      const expired = await newInvite({ expiresIn: "1 hour" });
      await as("owner");
      await db.query("update public.invites set expires_at = now() - interval '1 second' where id = $1", [expired.id]);
      const valid = await one<{ code: string }>("select code from public.invites where id = $1", [expired.id]);

      await as(applicant);
      await fails("select public.redeem_invite($1)", [revoked.code], INVITE_UNUSABLE, /invite_revoked/);
      await fails("select public.redeem_invite($1)", [valid.code], INVITE_UNUSABLE, /invite_expired/);
      await fails("select public.redeem_invite('ffffffffffffffff')", [], INVITE_UNUSABLE, /invite_unknown/);

      await as(admin);
      const fresh = await newInvite();
      for (const who of ["anon", creator, team]) {
        await as(who);
        await fails("select public.redeem_invite($1)", [fresh.code], PERMISSION_DENIED);
      }
    });
  });

  it("counts one use per person, however often they tap", async () => {
    const newcomer = await createUser(db);
    await scenario(async (as) => {
      await as(admin);
      const invite = await newInvite({ maxUses: 5 });
      await as(newcomer);
      await db.query("select public.redeem_invite($1)", [invite.code]);
      await fails("select public.redeem_invite($1)", [invite.code], PERMISSION_DENIED);
      await as("owner");
      expect(await one("select uses from public.invites where id = $1", [invite.id])).toEqual({ uses: 1 });
    });
  });

  it("doesn't overturn a rejection", async () => {
    const { applicant, applicationId } = await (async () => {
      const id = await createUser(db);
      await db.query("begin");
      await db.query("set local role authenticated");
      await db.query("select set_config('request.jwt.claims', $1, true)", [JSON.stringify({ sub: id, role: "authenticated" })]);
      const { rows: [result] } = await apply({ x_handle: `r${randomUUID().slice(0, 8)}` });
      await db.query("commit");
      return { applicant: id, applicationId: result.application_id as string };
    })();
    await scenario(async (as) => {
      await as(team);
      await db.query("select public.review_application($1, 'reject')", [applicationId]);
      await as(admin);
      const invite = await newInvite();
      await as(applicant);
      await fails("select public.redeem_invite($1)", [invite.code], CONFLICT, /application_rejected/);
      await as("owner");
      expect(await one("select uses from public.invites where id = $1", [invite.id])).toEqual({ uses: 0 });
      expect(await one("select role from public.profiles where id = $1", [applicant])).toEqual({ role: "applicant" });
    });
  });
});

describe("payout details", () => {
  function setPayout(values: Record<string, string | null>) {
    const v = {
      method: null,
      asset: null,
      network: null,
      wallet: null,
      bank_country: null,
      bank_name: null,
      account_name: null,
      account_number: null,
      bank_code: null,
      other: null,
      ...values,
    };
    return db.query<{ id: string }>(
      `select public.set_payout_details(
         p_method => $1, p_crypto_asset => $2, p_crypto_network => $3, p_wallet_address => $4,
         p_bank_country => $5, p_bank_name => $6, p_account_name => $7, p_account_number => $8,
         p_bank_code => $9, p_other_details => $10) as id`,
      [v.method, v.asset, v.network, v.wallet, v.bank_country, v.bank_name, v.account_name, v.account_number, v.bank_code, v.other],
    );
  }

  it("saves a wallet, emails the creator a masked summary and logs no details", async () => {
    await scenario(async (as) => {
      await as(creator);
      const { rows: [{ id }] } = await setPayout({ method: "crypto", asset: "usdc", network: "Base", wallet: ` ${EVM} ` });
      expect(await rows("select method, crypto_asset, crypto_network, wallet_address from public.payout_details")).toEqual([
        { method: "crypto", crypto_asset: "USDC", crypto_network: "base", wallet_address: EVM },
      ]);

      await as("owner");
      expect(await one("select recipient, template, payload from public.outbox where id = $1", [id])).toEqual({
        recipient: creatorEmail,
        template: "payout_details_changed",
        payload: { summary: "USDC on Base, wallet ending 9EE7", profile_id: creator },
      });
      const log = await one<{ action: string; details: Record<string, unknown> }>(
        "select action, details from public.activity_log where actor = $1 and action = 'payout_details.changed'",
        [creator],
      );
      expect(log).toEqual({ action: "payout_details.changed", details: { method: "crypto" } });
      expect(JSON.stringify(log)).not.toContain(EVM);
    });
  });

  it("allows ten changes an hour, since each one sends an email", async () => {
    await scenario(async (as) => {
      await as(creator);
      for (let i = 0; i < 10; i += 1) await setPayout({ method: "other", other: `PayPal ${i}` });
      await fails(
        "select public.set_payout_details(p_method => 'other', p_other_details => 'PayPal 11')",
        [],
        "P0429",
        /rate_limited/,
      );
    });
  });

  it("keeps the change emails, which name the bank or network, from team", async () => {
    await scenario(async (as) => {
      await as(creator);
      const { rows: [{ id }] } = await setPayout({ method: "crypto", asset: "USDC", network: "base", wallet: EVM });
      await as(team);
      expect(await rows("select id from public.outbox where id = $1", [id])).toEqual([]);
      await as(admin);
      expect(await rows("select id from public.outbox where id = $1", [id])).toEqual([{ id }]);
    });
  });

  it("checks the address against its network", async () => {
    await scenario(async (as) => {
      await as(creator);
      await setPayout({ method: "crypto", asset: "USDC", network: "solana", wallet: SOLANA });
      await setPayout({ method: "crypto", asset: "USDT", network: "tron", wallet: TRON });
      for (const [network, wallet, asset] of [
        ["base", SOLANA, "USDC"],
        ["solana", EVM, "USDC"],
        ["tron", EVM, "USDT"],
        ["ethereum", "0x123", "USDC"],
        ["base", EVM, "USDT"],
        ["tron", TRON, "USDC"],
      ]) {
        await db.query("savepoint attempt");
        await expect(setPayout({ method: "crypto", asset, network, wallet }), `${asset} on ${network}`).rejects.toMatchObject({
          code: CHECK_VIOLATION,
        });
        await db.query("rollback to savepoint attempt");
      }
    });
  });

  it("switches method cleanly, keeping only the new method's fields", async () => {
    await scenario(async (as) => {
      await as(creator);
      await setPayout({ method: "crypto", asset: "USDC", network: "base", wallet: EVM });
      const { rows: [{ id }] } = await setPayout({
        method: "bank",
        bank_country: "ng",
        bank_name: "GTBank",
        account_name: "Amara Okafor",
        account_number: "GB29 NWBK 6016 1331 9268 19",
        // Fields of other methods are dropped, whatever the form sent.
        wallet: EVM,
      });
      expect(await one("select method, wallet_address, bank_country, account_number from public.payout_details")).toEqual({
        method: "bank",
        wallet_address: null,
        bank_country: "NG",
        account_number: "GB29 NWBK 6016 1331 9268 19",
      });
      await as("owner");
      expect(await one("select payload from public.outbox where id = $1", [id])).toEqual({
        // The spaces in an IBAN don't count: the same ending the profile page shows.
        payload: { summary: "GTBank, account ending 6819", profile_id: creator },
      });
      await as(creator);
      await setPayout({ method: "other", other: "PayPal: amara@example.com" });
      expect(await one("select method, bank_name, other_details from public.payout_details")).toEqual({
        method: "other",
        bank_name: null,
        other_details: "PayPal: amara@example.com",
      });
    });
  });

  it("lets only creators set them, and only through the function", async () => {
    const applicant = await createUser(db);
    await scenario(async (as) => {
      for (const who of ["anon", applicant, team]) {
        await as(who);
        await fails("select public.set_payout_details('other', p_other_details => 'x')", [], PERMISSION_DENIED);
      }
      await as(creator);
      await fails("select public.set_payout_details('cash')", [], INVALID_PARAMETER);
      await fails(
        "insert into public.payout_details (profile_id, method, other_details) values ($1, 'other', 'x')",
        [creator],
        PERMISSION_DENIED,
      );
    });
  });

  it("shows them to the creator and the admin, never to team or other creators", async () => {
    const another = await createUser(db);
    await setProfile(db, another, { role: "creator" });
    await scenario(async (as) => {
      await as(creator);
      await setPayout({ method: "other", other: "Wise: amara@example.com" });
      expect(await rows("select profile_id from public.payout_details")).toEqual([{ profile_id: creator }]);
      await as(admin);
      expect(await rows("select profile_id from public.payout_details")).toEqual([{ profile_id: creator }]);
      for (const who of [team, another]) {
        await as(who);
        expect(await rows("select profile_id from public.payout_details"), who).toEqual([]);
      }
    });
  });
});

describe("my_referrals", () => {
  it("counts who applied with the caller's link, and how many were approved", async () => {
    const referrer = await createUser(db);
    const first = await createUser(db);
    const second = await createUser(db);
    await scenario(async (as) => {
      await as("owner");
      await setProfile(db, referrer, { role: "creator" });
      await db.query("update public.profiles set referred_by = $1 where id in ($2, $3)", [referrer, first, second]);
      await setProfile(db, second, { role: "creator" });
      await as(referrer);
      expect(await one("select * from public.my_referrals()")).toEqual({ applied: 2, approved: 1 });
      await as(first);
      expect(await one("select * from public.my_referrals()")).toEqual({ applied: 0, approved: 0 });
    });
  });
});
