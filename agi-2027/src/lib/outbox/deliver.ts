import "server-only";

import type { SupabaseClient } from "@supabase/supabase-js";

import { leadReceivedEmail, type LeadEmailData } from "@/lib/email/lead-received";
import { sendEmail, type EmailMessage } from "@/lib/email/resend";
import { siteConfig } from "@/lib/site";
import { createAdminClient } from "@/lib/supabase/admin";
import { getSupabaseEnv } from "@/lib/supabase/env";

/** A row of public.outbox, as claim_outbox returns it. */
export type OutboxRow = {
  id: string;
  channel: string;
  recipient: string;
  template: string;
  payload: Record<string, unknown> | null;
  attempts: number;
};

export type DeliverSummary = {
  /** Rows this run picked up. */
  claimed: number;
  sent: number;
  /** Rows that failed this attempt. finish_outbox retries them later, up to five attempts in all. */
  failed: number;
  /** Set when the run couldn't start, such as Supabase not being configured. */
  error?: string;
};

type Attempt = { ok: true } | { ok: false; error: string };

/** How many emails go out at once. Small, so a run stays well inside a function's time limit. */
const CONCURRENCY = 5;

const LEAD_COLUMNS =
  "id, name, email, company, website, x_handle, launching, launch_date, budget, message, source, created_at";

/**
 * Sends queued messages: claims due rows with public.claim_outbox (row locks,
 * so two runs never send the same row), sends each one, then records the
 * result with public.finish_outbox, which schedules retries with backoff.
 * Never throws, and never logs names or addresses.
 */
export async function deliverOutbox({ id, limit = 10 }: { id?: string; limit?: number } = {}): Promise<DeliverSummary> {
  const summary: DeliverSummary = { claimed: 0, sent: 0, failed: 0 };
  if (!getSupabaseEnv() || !process.env.SUPABASE_SECRET_KEY) {
    return { ...summary, error: "Supabase isn't configured, so there is no outbox to read." };
  }

  let admin: SupabaseClient;
  let rows: OutboxRow[];
  try {
    admin = createAdminClient();
    const { data, error } = await admin.rpc("claim_outbox", {
      p_limit: Math.max(1, Math.min(Math.trunc(limit), 50)),
      p_id: id ?? null,
    });
    if (error) {
      console.error(`[outbox] claim_outbox failed: ${error.code ?? "no code"} ${error.message}`);
      return { ...summary, error: "Couldn't claim outbox rows." };
    }
    rows = (Array.isArray(data) ? data : data ? [data] : []) as OutboxRow[];
  } catch (error) {
    console.error(`[outbox] claim_outbox threw: ${error instanceof Error ? error.name : "unknown error"}`);
    return { ...summary, error: "Couldn't claim outbox rows." };
  }

  summary.claimed = rows.length;
  for (let i = 0; i < rows.length; i += CONCURRENCY) {
    const batch = rows.slice(i, i + CONCURRENCY);
    const results = await Promise.all(batch.map((row) => deliverRow(admin, row)));
    for (const ok of results) {
      if (ok) summary.sent += 1;
      else summary.failed += 1;
    }
  }
  return summary;
}

/** Sends one row and records the outcome. Returns true when the email went out. */
async function deliverRow(admin: SupabaseClient, row: OutboxRow): Promise<boolean> {
  let attempt: Attempt;
  try {
    attempt = await attemptRow(admin, row);
  } catch (error) {
    attempt = { ok: false, error: `Unexpected error: ${error instanceof Error ? error.name : "unknown"}` };
  }

  if (!attempt.ok) {
    // The row id and attempt number are enough to find it; the error text can hold addresses.
    console.warn(`[outbox] ${row.template} ${row.id} not sent (attempt ${row.attempts})`);
  }

  try {
    const { error } = await admin.rpc("finish_outbox", {
      p_id: row.id,
      p_ok: attempt.ok,
      p_error: attempt.ok ? null : attempt.error.slice(0, 1000),
    });
    if (error) console.error(`[outbox] finish_outbox failed for ${row.id}: ${error.code ?? "no code"}`);
  } catch (error) {
    // The row stays in 'sending'; claim_outbox picks it up again once it goes stale.
    console.error(`[outbox] finish_outbox threw for ${row.id}: ${error instanceof Error ? error.name : "unknown"}`);
  }
  return attempt.ok;
}

async function attemptRow(admin: SupabaseClient, row: OutboxRow): Promise<Attempt> {
  if (row.channel !== "email") return { ok: false, error: `Channel "${row.channel}" isn't supported yet.` };

  const to = resolveRecipient(row.recipient);
  if (!to.ok) return to;
  if (!process.env.RESEND_API_KEY) {
    return { ok: false, error: "RESEND_API_KEY is not set, so no email was sent. The lead is saved." };
  }

  const message = await buildMessage(admin, row);
  if (!message.ok) return message;

  const sent = await sendEmail({ ...message.email, to: to.address, idempotencyKey: `outbox-${row.id}` });
  return sent.ok ? { ok: true } : { ok: false, error: sent.error };
}

/** 'owner' means the agency's inbox for new leads; anything else is an address. */
function resolveRecipient(recipient: string): { ok: true; address: string } | { ok: false; error: string } {
  if (recipient === "owner") {
    const address = process.env.LEADS_NOTIFY_EMAIL?.trim();
    return address
      ? { ok: true, address }
      : { ok: false, error: "LEADS_NOTIFY_EMAIL is not set, so there is no inbox for owner emails." };
  }
  return recipient.includes("@")
    ? { ok: true, address: recipient }
    : { ok: false, error: `Unknown recipient "${recipient}".` };
}

type BuiltMessage = { ok: true; email: Omit<EmailMessage, "to"> } | { ok: false; error: string };

async function buildMessage(admin: SupabaseClient, row: OutboxRow): Promise<BuiltMessage> {
  switch (row.template) {
    case "lead_received": {
      const leadId = row.payload?.lead_id;
      if (typeof leadId !== "string") return { ok: false, error: "The payload has no lead_id." };
      const { data, error } = await admin.from("leads").select(LEAD_COLUMNS).eq("id", leadId).maybeSingle();
      if (error) return { ok: false, error: `Couldn't load the lead: ${error.code ?? error.message}` };
      if (!data) return { ok: false, error: "The lead no longer exists." };
      const lead = data as LeadEmailData;
      const rendered = leadReceivedEmail(lead, { siteUrl: siteConfig.url });
      // Replies go straight to the person who booked.
      return { ok: true, email: { ...rendered, replyTo: lead.email } };
    }
    default:
      return { ok: false, error: `Unknown template "${row.template}".` };
  }
}
