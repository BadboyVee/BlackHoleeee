import { randomUUID } from "node:crypto";

import type { Client } from "pg";
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { asAnon, asService, asUser, connect, createUser, PERMISSION_DENIED, setProfile } from "./helpers";

/*
 * Milestone 2: leads, the outbox, the activity log and rate limits
 * (supabase/migrations/20261012000000_leads_outbox.sql).
 */

const CHECK_VIOLATION = "23514";
const NOT_NULL_VIOLATION = "23502";
const INVALID_TEXT = "22P02";
const RATE_LIMITED = "P0429";

let db: Client;
const users: Record<"creator" | "applicant" | "team" | "admin" | "suspendedAdmin", string> = {
  creator: "",
  applicant: "",
  team: "",
  admin: "",
  suspendedAdmin: "",
};

type LeadInput = {
  name: string | null;
  email: string | null;
  company: string | null;
  website: string | null;
  x_handle: string | null;
  launching: string | null;
  launch_date: string | null;
  budget: string | null;
  message: string | null;
  source: string | null;
  rate_key: string | null;
};

const validLead = (): LeadInput => ({
  name: "Ada Lovelace",
  email: "ada@kled.ai",
  company: "Kled",
  website: "https://kled.ai",
  x_handle: "kled_ai",
  launching: "An app that pays people for their data.",
  launch_date: "2026-11-02",
  budget: "10k_25k",
  message: "We launch in three weeks.",
  source: "book_page",
  rate_key: randomUUID(),
});

/** Calls submit_lead with named arguments, exactly as the app does through PostgREST. */
async function submitLead(values: Partial<LeadInput> = {}) {
  const v = { ...validLead(), ...values };
  const { rows } = await db.query<{ lead_id: string; outbox_id: string }>(
    `select * from public.submit_lead(
       p_name => $1, p_email => $2, p_company => $3, p_website => $4, p_x_handle => $5,
       p_launching => $6, p_launch_date => $7::date, p_budget => $8, p_message => $9,
       p_source => $10, p_rate_key => $11)`,
    [v.name, v.email, v.company, v.website, v.x_handle, v.launching, v.launch_date, v.budget, v.message, v.source, v.rate_key],
  );
  return rows;
}

/** Inside an asService block: does a step as the database owner, then goes back to service_role. */
async function asOwner<T>(fn: () => Promise<T>) {
  await db.query("reset role");
  try {
    return await fn();
  } finally {
    await db.query("set local role service_role");
  }
}

/** Adds an outbox row as the database owner. `sendAfter` and `updatedAt` are SQL expressions. */
async function queueRow(
  client: Client,
  {
    status = "pending",
    attempts = 0,
    sendAfter = "now()",
    updatedAt = "now()",
    template = "lead_received",
  }: { status?: string; attempts?: number; sendAfter?: string; updatedAt?: string; template?: string } = {},
) {
  const { rows } = await client.query<{ id: string }>(
    `insert into public.outbox (recipient, template, payload, status, attempts, send_after, updated_at, sent_at)
     values ('owner', $1, '{}'::jsonb, $2, $3, ${sendAfter}, ${updatedAt}, case when $2 = 'sent' then now() end)
     returning id`,
    [template, status, attempts],
  );
  return rows[0].id;
}

async function claim(client: Client, limit: number | null = 10, id: string | null = null) {
  const { rows } = await client.query("select * from public.claim_outbox($1, $2)", [limit, id]);
  return rows;
}

async function finish(id: string, ok: boolean, error: string | null = null) {
  await db.query("select public.finish_outbox($1, $2, $3)", [id, ok, error]);
}

async function outboxRow(id: string) {
  const { rows } = await db.query(
    `select status, attempts, last_error, sent_at is not null as has_sent_at,
            sent_at = now() as sent_now, updated_at = now() as touched_now,
            round(extract(epoch from (send_after - now())) / 60)::int as due_in_minutes
     from public.outbox where id = $1`,
    [id],
  );
  return rows[0];
}

beforeAll(async () => {
  db = await connect();
  users.creator = await createUser(db);
  await setProfile(db, users.creator, { role: "creator" });
  users.applicant = await createUser(db);
  users.team = await createUser(db);
  await setProfile(db, users.team, { role: "team" });
  users.admin = await createUser(db);
  await setProfile(db, users.admin, { role: "admin" });
  users.suspendedAdmin = await createUser(db);
  await setProfile(db, users.suspendedAdmin, { role: "admin", status: "suspended" });
});

afterAll(async () => {
  await db.end();
});

describe("the schema", () => {
  it("has row level security on every new table", async () => {
    const { rows } = await db.query(
      `select relname, relrowsecurity from pg_class
       where oid in ('public.leads'::regclass, 'public.outbox'::regclass,
                     'public.activity_log'::regclass, 'public.rate_limits'::regclass)
       order by relname`,
    );
    expect(rows).toEqual([
      { relname: "activity_log", relrowsecurity: true },
      { relname: "leads", relrowsecurity: true },
      { relname: "outbox", relrowsecurity: true },
      { relname: "rate_limits", relrowsecurity: true },
    ]);
  });

  it("runs every function as its owner with an empty search_path", async () => {
    const { rows } = await db.query(
      `select p.proname, p.prosecdef, p.proconfig
       from pg_proc p join pg_namespace n on n.oid = p.pronamespace
       where (n.nspname, p.proname) in (('public', 'submit_lead'), ('public', 'claim_outbox'),
         ('public', 'finish_outbox'), ('private', 'take_rate_limit'), ('private', 'log_activity'))
       order by p.proname`,
    );
    expect(rows).toHaveLength(5);
    for (const row of rows) {
      expect(row.prosecdef, row.proname).toBe(true);
      expect(row.proconfig, row.proname).toEqual(['search_path=""']);
    }
  });
});

describe("who can see and change leads", () => {
  let leadId: string;
  let outboxId: string;

  beforeAll(async () => {
    // Saved for real (no rollback) so every caller below has a lead to look for.
    [{ lead_id: leadId, outbox_id: outboxId }] = await submitLead({ company: "Seeded Co" });
  });

  it("shows signed-out visitors nothing, and lets them change nothing", async () => {
    for (const sql of [
      "select id from public.leads",
      "select id from public.outbox",
      "select id from public.activity_log",
      "select bucket from public.rate_limits",
      "insert into public.leads (name, email, company, launching, budget, source) values ('a', 'a@b.co', 'c', 'd', 'not_sure', 'book_page')",
      "update public.leads set status = 'won'",
      "delete from public.leads",
    ]) {
      await expect(asAnon(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
  });

  it("hides leads, the outbox and the activity log from creators, applicants and suspended staff", async () => {
    for (const who of ["creator", "applicant", "suspendedAdmin"] as const) {
      const counts = await asUser(db, users[who], async () => {
        const { rows } = await db.query(
          `select (select count(*) from public.leads)::int as leads,
                  (select count(*) from public.outbox)::int as outbox,
                  (select count(*) from public.activity_log)::int as activity`,
        );
        return rows[0];
      });
      expect(counts, who).toEqual({ leads: 0, outbox: 0, activity: 0 });
    }
  });

  it("ignores status and notes changes from anyone who isn't staff", async () => {
    for (const who of ["creator", "applicant", "suspendedAdmin"] as const) {
      const updated = await asUser(db, users[who], async () => {
        const result = await db.query("update public.leads set status = 'won', notes = 'mine' where id = $1", [leadId]);
        return result.rowCount;
      });
      expect(updated, who).toBe(0);
    }
    const { rows } = await db.query("select status, notes from public.leads where id = $1", [leadId]);
    expect(rows[0]).toEqual({ status: "new", notes: "" });
  });

  it("lets team and admin read leads, the outbox and the activity log", async () => {
    for (const who of ["team", "admin"] as const) {
      const seen = await asUser(db, users[who], async () => {
        const lead = await db.query("select company from public.leads where id = $1", [leadId]);
        const outbox = await db.query("select template from public.outbox where id = $1", [outboxId]);
        const activity = await db.query(
          "select action from public.activity_log where entity_type = 'lead' and entity_id = $1",
          [leadId],
        );
        return { lead: lead.rows, outbox: outbox.rows, activity: activity.rows };
      });
      expect(seen, who).toEqual({
        lead: [{ company: "Seeded Co" }],
        outbox: [{ template: "lead_received" }],
        activity: [{ action: "lead.created" }],
      });
    }
  });

  it("lets team and admin move a lead along and keep notes", async () => {
    for (const [who, status] of [
      ["team", "contacted"],
      ["admin", "won"],
    ] as const) {
      const row = await asUser(db, users[who], async () => {
        const result = await db.query(
          "update public.leads set status = $2, notes = 'Called on Monday.' where id = $1 returning status, notes, updated_at > created_at as touched",
          [leadId, status],
        );
        return result.rows[0];
      });
      expect(row, who).toEqual({ status, notes: "Called on Monday.", touched: true });
    }
  });

  it("keeps staff notes to a sane length", async () => {
    await expect(
      asUser(db, users.admin, () =>
        db.query("update public.leads set notes = $2 where id = $1", [leadId, "x".repeat(5001)]),
      ),
    ).rejects.toMatchObject({ code: CHECK_VIOLATION });
  });

  it("never lets staff change what the person sent, or add and delete leads", async () => {
    for (const who of ["team", "admin"] as const) {
      for (const sql of [
        "update public.leads set name = 'Someone else' where id = $1",
        "update public.leads set email = 'other@example.com' where id = $1",
        "update public.leads set budget = '25k_plus' where id = $1",
        "update public.leads set source = 'home_cta' where id = $1",
        "update public.leads set created_at = now() where id = $1",
        "delete from public.leads where id = $1",
        "insert into public.leads (id, name, email, company, launching, budget, source) values ($1, 'a', 'a@b.co', 'c', 'd', 'not_sure', 'book_page')",
      ]) {
        await expect(asUser(db, users[who], () => db.query(sql, [leadId])), `${who}: ${sql}`).rejects.toMatchObject({
          code: PERMISSION_DENIED,
        });
      }
    }
  });

  it("never lets staff write to the outbox or the activity log, or see rate limits", async () => {
    for (const who of ["team", "admin"] as const) {
      for (const sql of [
        "update public.outbox set status = 'sent', sent_at = now()",
        "delete from public.outbox",
        "insert into public.outbox (recipient, template) values ('owner', 'lead_received')",
        "insert into public.activity_log (action) values ('lead.created')",
        "update public.activity_log set action = 'lead.deleted'",
        "delete from public.activity_log",
        "select bucket from public.rate_limits",
      ]) {
        await expect(asUser(db, users[who], () => db.query(sql)), `${who}: ${sql}`).rejects.toMatchObject({
          code: PERMISSION_DENIED,
        });
      }
    }
  });

  it("lets the service key read leads and the outbox, and write only through the functions", async () => {
    const seen = await asService(db, async () => {
      const lead = await db.query("select company from public.leads where id = $1", [leadId]);
      const outbox = await db.query("select status from public.outbox where id = $1", [outboxId]);
      const activity = await db.query("select count(*)::int as count from public.activity_log where entity_id = $1", [leadId]);
      return { lead: lead.rows[0], outbox: outbox.rows[0], activity: activity.rows[0].count };
    });
    expect(seen).toEqual({ lead: { company: "Seeded Co" }, outbox: { status: "pending" }, activity: 1 });

    for (const sql of [
      "insert into public.leads (name, email, company, launching, budget, source) values ('a', 'a@b.co', 'c', 'd', 'not_sure', 'book_page')",
      "update public.leads set status = 'won'",
      "delete from public.leads",
      "insert into public.outbox (recipient, template) values ('owner', 'lead_received')",
      "update public.outbox set status = 'sent', sent_at = now()",
      "delete from public.outbox",
      "insert into public.activity_log (action) values ('lead.created')",
      "update public.activity_log set action = 'lead.deleted'",
      "delete from public.activity_log",
      "select bucket from public.rate_limits",
      "insert into public.rate_limits (bucket, window_start, hits) values ('x', now(), 0)",
    ]) {
      await expect(asService(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
  });
});

describe("who can call the functions", () => {
  const publicCalls = [
    "select * from public.submit_lead('Ada', 'ada@kled.ai', 'Kled', null, null, 'A big launch soon.', null, 'not_sure', null, 'book_page', 'key')",
    "select * from public.claim_outbox()",
    "select public.finish_outbox(gen_random_uuid(), true)",
  ];

  it("keeps submit_lead and the outbox worker away from visitors", async () => {
    for (const sql of publicCalls) {
      await expect(asAnon(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
  });

  it("keeps them away from every signed-in role, staff included", async () => {
    for (const who of ["creator", "applicant", "team", "admin"] as const) {
      for (const sql of publicCalls) {
        await expect(asUser(db, users[who], () => db.query(sql)), `${who}: ${sql}`).rejects.toMatchObject({
          code: PERMISSION_DENIED,
        });
      }
    }
  });

  it("lets nobody call the private helpers directly, not even the service key", async () => {
    const helpers = [
      "select private.take_rate_limit('x', 5, interval '1 hour')",
      "select private.log_activity(null, 'lead.created', 'lead', 'x', '{}'::jsonb)",
    ];
    for (const sql of helpers) {
      await expect(asAnon(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
      await expect(asUser(db, users.admin, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
      await expect(asService(db, () => db.query(sql)), sql).rejects.toMatchObject({ code: PERMISSION_DENIED });
    }
  });
});

describe("submit_lead", () => {
  it("saves the lead, queues the owner's email and logs it, in one call", async () => {
    const result = await asService(db, async () => {
      const [ids] = await submitLead({ source: "home_cta" });
      const lead = await db.query(
        `select name, email, company, website, x_handle, launching, launch_date::text, budget, message,
                source, status, notes, created_at = now() as created_now, updated_at = now() as updated_now
         from public.leads where id = $1`,
        [ids.lead_id],
      );
      const outbox = await db.query(
        `select channel, recipient, template, payload, status, attempts, last_error, sent_at,
                send_after <= now() as due
         from public.outbox where id = $1`,
        [ids.outbox_id],
      );
      const activity = await db.query(
        "select actor, action, entity_type, entity_id, details from public.activity_log where entity_id = $1",
        [ids.lead_id],
      );
      return { ids, lead: lead.rows, outbox: outbox.rows, activity: activity.rows };
    });

    expect(result.ids.lead_id).toMatch(/^[0-9a-f-]{36}$/);
    expect(result.lead).toEqual([
      {
        name: "Ada Lovelace",
        email: "ada@kled.ai",
        company: "Kled",
        website: "https://kled.ai",
        x_handle: "kled_ai",
        launching: "An app that pays people for their data.",
        launch_date: "2026-11-02",
        budget: "10k_25k",
        message: "We launch in three weeks.",
        source: "home_cta",
        status: "new",
        notes: "",
        created_now: true,
        updated_now: true,
      },
    ]);
    expect(result.outbox).toEqual([
      {
        channel: "email",
        recipient: "owner",
        template: "lead_received",
        payload: { lead_id: result.ids.lead_id },
        status: "pending",
        attempts: 0,
        last_error: null,
        sent_at: null,
        due: true,
      },
    ]);
    expect(result.activity).toEqual([
      {
        actor: null,
        action: "lead.created",
        entity_type: "lead",
        entity_id: result.ids.lead_id,
        details: { source: "home_cta", company: "Kled" },
      },
    ]);
  });

  it("trims text and stores empty optional fields as null", async () => {
    const lead = await asService(db, async () => {
      const [{ lead_id }] = await submitLead({
        name: "  Ada  ",
        email: " ada@kled.ai ",
        company: " Kled ",
        website: "  ",
        x_handle: "",
        launch_date: null,
        message: "   ",
      });
      const { rows } = await db.query(
        "select name, email, company, website, x_handle, launch_date, message from public.leads where id = $1",
        [lead_id],
      );
      return rows[0];
    });
    expect(lead).toEqual({
      name: "Ada",
      email: "ada@kled.ai",
      company: "Kled",
      website: null,
      x_handle: null,
      launch_date: null,
      message: null,
    });
  });

  it("accepts values right at the limits", async () => {
    const saved = await asService(db, async () => {
      const rows = await submitLead({
        name: "n".repeat(80),
        email: `${"e".repeat(244)}@kled.ai`,
        company: "c".repeat(120),
        website: `http://kled.ai/${"p".repeat(2048 - 15)}`,
        x_handle: "A".repeat(15),
        launching: "l".repeat(600),
        message: "m".repeat(2000),
        budget: "not_sure",
      });
      return rows.length;
    });
    expect(saved).toBe(1);
  });

  it("allows 5 requests an hour per rate key, then refuses with P0429 while other keys still work", async () => {
    const key = randomUUID();
    const outcome = await asService(db, async () => {
      for (let i = 0; i < 5; i += 1) await submitLead({ rate_key: key });

      await db.query("savepoint sixth");
      let error: unknown;
      try {
        await submitLead({ rate_key: key, company: "Sixth Co" });
      } catch (caught) {
        error = caught;
      }
      await db.query("rollback to savepoint sixth");

      const otherKey = await submitLead({ rate_key: randomUUID(), company: "Other Co" });
      const companies = await db.query(
        "select company, count(*)::int as count from public.leads where company in ('Kled', 'Sixth Co', 'Other Co') and created_at = now() group by company order by company",
      );
      const hits = await asOwner(() =>
        db.query("select hits from public.rate_limits where bucket = $1", [`lead:${key}`]),
      );
      return { error, otherKey: otherKey.length, companies: companies.rows, hits: hits.rows };
    });

    expect(outcome.error).toMatchObject({ code: RATE_LIMITED, message: "rate_limited" });
    expect(outcome.otherKey).toBe(1);
    expect(outcome.companies).toEqual([
      { company: "Kled", count: 5 },
      { company: "Other Co", count: 1 },
    ]);
    expect(outcome.hits).toEqual([{ hits: 5 }]);
  });

  it("forgets hits from an earlier hour", async () => {
    const key = randomUUID();
    const buckets = await asService(db, async () => {
      await asOwner(() =>
        db.query(
          `insert into public.rate_limits (bucket, window_start, hits)
           values ($1, date_bin('1 hour', now(), timestamptz '1970-01-01 00:00:00+00') - interval '1 hour', 99)`,
          [`lead:${key}`],
        ),
      );
      await submitLead({ rate_key: key });
      return asOwner(async () => {
        const { rows } = await db.query(
          `select hits, window_start = date_bin('1 hour', now(), timestamptz '1970-01-01 00:00:00+00') as current
           from public.rate_limits where bucket = $1`,
          [`lead:${key}`],
        );
        return rows;
      });
    });
    expect(buckets).toEqual([{ hits: 1, current: true }]);
  });

  it("puts requests without a rate key in one shared bucket instead of skipping the limit", async () => {
    const error = await asService(db, async () => {
      await asOwner(() => db.query("delete from public.rate_limits where bucket = 'lead:unknown'"));
      for (const key of [null, "", "  ", null, ""]) await submitLead({ rate_key: key });
      return submitLead({ rate_key: null }).then(
        () => null,
        (caught: unknown) => caught,
      );
    });
    expect(error).toMatchObject({ code: RATE_LIMITED });
  });

  const tooLong = (n: number) => "x".repeat(n);
  const badInputs: [string, Partial<LeadInput>, string][] = [
    ["an empty name", { name: "" }, CHECK_VIOLATION],
    ["a blank name", { name: "   " }, CHECK_VIOLATION],
    ["no name", { name: null }, NOT_NULL_VIOLATION],
    ["a name over 80 characters", { name: tooLong(81) }, CHECK_VIOLATION],
    ["an email without an @", { email: "ada.kled.ai" }, CHECK_VIOLATION],
    ["an email with a space", { email: "ada lovelace@kled.ai" }, CHECK_VIOLATION],
    ["an email over 254 characters", { email: `${tooLong(247)}@kled.ai` }, CHECK_VIOLATION],
    ["an empty company", { company: "" }, CHECK_VIOLATION],
    ["a company over 120 characters", { company: tooLong(121) }, CHECK_VIOLATION],
    ["a javascript: website", { website: "javascript:alert(1)" }, CHECK_VIOLATION],
    ["a data: website", { website: "data:text/html,hi" }, CHECK_VIOLATION],
    ["an ftp website", { website: "ftp://kled.ai" }, CHECK_VIOLATION],
    ["a website without a scheme", { website: "kled.ai" }, CHECK_VIOLATION],
    ["a website with a space", { website: "https://kled.ai/a b" }, CHECK_VIOLATION],
    ["a website over 2048 characters", { website: `https://kled.ai/${tooLong(2033)}` }, CHECK_VIOLATION],
    ["a handle with an @", { x_handle: "@kled_ai" }, CHECK_VIOLATION],
    ["a handle with a space", { x_handle: "kled ai" }, CHECK_VIOLATION],
    ["a handle over 15 characters", { x_handle: tooLong(16) }, CHECK_VIOLATION],
    ["a handle with a dash", { x_handle: "kled-ai" }, CHECK_VIOLATION],
    ["an empty launch description", { launching: "" }, CHECK_VIOLATION],
    ["a launch description over 600 characters", { launching: tooLong(601) }, CHECK_VIOLATION],
    ["a message over 2000 characters", { message: tooLong(2001) }, CHECK_VIOLATION],
    ["an unknown budget", { budget: "a_lot" }, INVALID_TEXT],
    ["no budget", { budget: null }, NOT_NULL_VIOLATION],
    ["an unknown source", { source: "twitter" }, CHECK_VIOLATION],
    ["no source", { source: null }, NOT_NULL_VIOLATION],
  ];

  it.each(badInputs)("rejects %s", async (_label, values, code) => {
    await expect(asService(db, () => submitLead(values))).rejects.toMatchObject({ code });
  });

  it("saves nothing when a value is rejected", async () => {
    const counts = await asService(db, async () => {
      const before = await db.query(
        "select (select count(*) from public.leads)::int as leads, (select count(*) from public.outbox)::int as outbox, (select count(*) from public.activity_log)::int as activity",
      );
      await db.query("savepoint bad");
      await submitLead({ website: "javascript:alert(1)" }).catch(() => null);
      await db.query("rollback to savepoint bad");
      const after = await db.query(
        "select (select count(*) from public.leads)::int as leads, (select count(*) from public.outbox)::int as outbox, (select count(*) from public.activity_log)::int as activity",
      );
      return { before: before.rows[0], after: after.rows[0] };
    });
    expect(counts.after).toEqual(counts.before);
  });
});

describe("the outbox worker", () => {
  beforeEach(async () => {
    // Committed rows from other tests would change what a claim returns.
    await db.query("delete from public.outbox");
  });

  it("claims due rows oldest first, marks them sending and counts the attempt", async () => {
    const result = await asService(db, async () => {
      const ids = await asOwner(async () => ({
        newer: await queueRow(db, { sendAfter: "now() - interval '1 minute'" }),
        older: await queueRow(db, { sendAfter: "now() - interval '2 minutes'" }),
        future: await queueRow(db, { sendAfter: "now() + interval '1 hour'" }),
        sent: await queueRow(db, { status: "sent", attempts: 1, sendAfter: "now() - interval '1 hour'" }),
        failed: await queueRow(db, { status: "failed", attempts: 5, sendAfter: "now() - interval '1 hour'" }),
        // Claimed a minute ago by another worker that is still working on it.
        busy: await queueRow(db, { status: "sending", attempts: 1, updatedAt: "now() - interval '1 minute'" }),
      }));
      const claimed = await claim(db);
      return {
        ids,
        claimed: claimed.map((row) => ({ id: row.id, status: row.status, attempts: row.attempts })),
        older: await outboxRow(ids.older),
        future: await outboxRow(ids.future),
        busy: await outboxRow(ids.busy),
        again: await claim(db),
      };
    });

    expect(result.claimed).toEqual([
      { id: result.ids.older, status: "sending", attempts: 1 },
      { id: result.ids.newer, status: "sending", attempts: 1 },
    ]);
    expect(result.older).toMatchObject({ status: "sending", attempts: 1, touched_now: true });
    expect(result.future).toMatchObject({ status: "pending", attempts: 0 });
    expect(result.busy).toMatchObject({ status: "sending", attempts: 1, touched_now: false });
    expect(result.again).toEqual([]);
  });

  it("claims no more than p_limit rows, and at most 100", async () => {
    const counts = await asService(db, async () => {
      await asOwner(() =>
        db.query(
          "insert into public.outbox (recipient, template, send_after) select 'owner', 'lead_received', now() - interval '1 minute' from generate_series(1, 105)",
        ),
      );
      return {
        two: (await claim(db, 2)).length,
        zero: (await claim(db, 0)).length,
        negative: (await claim(db, -5)).length,
        huge: (await claim(db, 1000)).length,
        rest: (await claim(db, null)).length,
      };
    });
    expect(counts).toEqual({ two: 2, zero: 0, negative: 0, huge: 100, rest: 3 });
  });

  it("claims just the row named by p_id, and only when it is due", async () => {
    const result = await asService(db, async () => {
      const ids = await asOwner(async () => ({
        a: await queueRow(db),
        b: await queueRow(db),
        later: await queueRow(db, { sendAfter: "now() + interval '5 minutes'" }),
      }));
      return {
        ids,
        claimedB: (await claim(db, 10, ids.b)).map((row) => row.id),
        claimedLater: await claim(db, 10, ids.later),
        claimedBAgain: await claim(db, 10, ids.b),
        a: await outboxRow(ids.a),
      };
    });
    expect(result.claimedB).toEqual([result.ids.b]);
    expect(result.claimedLater).toEqual([]);
    expect(result.claimedBAgain).toEqual([]);
    expect(result.a).toMatchObject({ status: "pending", attempts: 0 });
  });

  it("never hands the same row to two workers at once", async () => {
    const ids = [await queueRow(db), await queueRow(db), await queueRow(db)];
    const other = await connect();
    // If a claim ever waited on a held row instead of skipping it, fail fast rather than hang.
    await other.query("set lock_timeout = '2s'");
    try {
      const { first, second, sameRow } = await asService(db, async () => {
        const firstClaim = await claim(db, 2);
        // A second worker on its own connection, while the first still holds its rows.
        const secondClaim = await asService(other, () => claim(other, 10));
        const contested = await asService(other, () => claim(other, 10, firstClaim[0].id));
        return {
          first: firstClaim.map((row) => row.id),
          second: secondClaim.map((row) => row.id),
          sameRow: contested,
        };
      });
      expect(first).toHaveLength(2);
      expect(second).toHaveLength(1);
      expect([...first, ...second].sort()).toEqual([...ids].sort());
      expect(sameRow).toEqual([]);
    } finally {
      await other.end();
      await db.query("delete from public.outbox");
    }
  });

  it("marks a row sent when delivery works", async () => {
    const row = await asService(db, async () => {
      const id = await asOwner(() => queueRow(db));
      await claim(db, 10, id);
      await finish(id, true);
      return outboxRow(id);
    });
    expect(row).toMatchObject({ status: "sent", attempts: 1, has_sent_at: true, sent_now: true, last_error: null });
  });

  it("backs off after each failure, then gives up after 5 attempts", async () => {
    const history = await asService(db, async () => {
      const id = await asOwner(() => queueRow(db));
      const steps = [];
      for (let attempt = 1; attempt <= 5; attempt += 1) {
        const claimed = await claim(db, 10, id);
        expect(claimed.map((row) => row.attempts)).toEqual([attempt]);
        await finish(id, false, `Resend said no (${attempt})`);
        const row = await outboxRow(id);
        steps.push({
          status: row.status,
          attempts: row.attempts,
          last_error: row.last_error,
          due_in_minutes: row.due_in_minutes,
          claimable_now: (await claim(db, 10, id)).length,
        });
        // Skip the wait: make the retry due right away.
        if (row.status === "pending") {
          await asOwner(() =>
            db.query("update public.outbox set send_after = now() - interval '1 second' where id = $1", [id]),
          );
        }
      }
      return steps;
    });

    expect(history).toEqual([
      { status: "pending", attempts: 1, last_error: "Resend said no (1)", due_in_minutes: 1, claimable_now: 0 },
      { status: "pending", attempts: 2, last_error: "Resend said no (2)", due_in_minutes: 4, claimable_now: 0 },
      { status: "pending", attempts: 3, last_error: "Resend said no (3)", due_in_minutes: 9, claimable_now: 0 },
      { status: "pending", attempts: 4, last_error: "Resend said no (4)", due_in_minutes: 16, claimable_now: 0 },
      // Failed rows keep the send_after of their last retry, which was moved back a second.
      { status: "failed", attempts: 5, last_error: "Resend said no (5)", due_in_minutes: 0, claimable_now: 0 },
    ]);
  });

  it("records a missing error as unknown and cuts long errors to 2000 characters", async () => {
    const rows = await asService(db, async () => {
      const [quiet, loud] = await asOwner(async () => [await queueRow(db), await queueRow(db)]);
      await claim(db);
      await finish(quiet, false, null);
      await finish(loud, false, "e".repeat(5000));
      return { quiet: await outboxRow(quiet), loud: await outboxRow(loud) };
    });
    expect(rows.quiet.last_error).toBe("Unknown error.");
    expect(rows.loud.last_error).toHaveLength(2000);
  });

  it("leaves rows alone that aren't being sent", async () => {
    const rows = await asService(db, async () => {
      const ids = await asOwner(async () => ({
        pending: await queueRow(db),
        sent: await queueRow(db, { status: "sent", attempts: 1 }),
        failed: await queueRow(db, { status: "failed", attempts: 5 }),
      }));
      await finish(ids.pending, true);
      await finish(ids.sent, false, "late failure");
      await finish(ids.failed, true);
      await finish(randomUUID(), true);
      return {
        pending: await outboxRow(ids.pending),
        sent: await outboxRow(ids.sent),
        failed: await outboxRow(ids.failed),
      };
    });
    expect(rows.pending).toMatchObject({ status: "pending", attempts: 0, has_sent_at: false });
    expect(rows.sent).toMatchObject({ status: "sent", last_error: null });
    expect(rows.failed).toMatchObject({ status: "failed", has_sent_at: false });
  });

  it("reclaims a send that stalled for over 15 minutes, and gives up on one with no attempts left", async () => {
    const result = await asService(db, async () => {
      const ids = await asOwner(async () => ({
        stalled: await queueRow(db, { status: "sending", attempts: 2, updatedAt: "now() - interval '16 minutes'" }),
        recent: await queueRow(db, { status: "sending", attempts: 2, updatedAt: "now() - interval '14 minutes'" }),
        exhausted: await queueRow(db, { status: "sending", attempts: 5, updatedAt: "now() - interval '16 minutes'" }),
      }));
      const claimed = await claim(db);
      return {
        ids,
        claimed: claimed.map((row) => ({ id: row.id, attempts: row.attempts })),
        stalled: await outboxRow(ids.stalled),
        recent: await outboxRow(ids.recent),
        exhausted: await outboxRow(ids.exhausted),
      };
    });
    expect(result.claimed).toEqual([{ id: result.ids.stalled, attempts: 3 }]);
    expect(result.stalled).toMatchObject({ status: "sending", attempts: 3, touched_now: true });
    expect(result.recent).toMatchObject({ status: "sending", attempts: 2, touched_now: false });
    expect(result.exhausted).toMatchObject({ status: "failed", attempts: 5 });
    expect(result.exhausted.last_error).toMatch(/never reported back/);
  });

  it("runs the queued lead email end to end", async () => {
    const row = await asService(db, async () => {
      const [{ lead_id, outbox_id }] = await submitLead();
      const claimed = await claim(db, 1, outbox_id);
      expect(claimed).toHaveLength(1);
      expect(claimed[0]).toMatchObject({ template: "lead_received", recipient: "owner", payload: { lead_id } });
      // The worker reads the lead to write the email.
      const lead = await db.query("select email from public.leads where id = $1", [claimed[0].payload.lead_id]);
      expect(lead.rows).toEqual([{ email: "ada@kled.ai" }]);
      await finish(outbox_id, true);
      return outboxRow(outbox_id);
    });
    expect(row).toMatchObject({ status: "sent", attempts: 1 });
  });
});
