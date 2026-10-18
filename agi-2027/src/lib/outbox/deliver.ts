import "server-only";

import type { SupabaseClient } from "@supabase/supabase-js";

import {
  applicationApprovedEmail,
  applicationReceivedEmail,
  applicationRejectedEmail,
  payoutDetailsChangedEmail,
} from "@/lib/email/creator-emails";
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
    case "application_received": {
      const applicationId = row.payload?.application_id;
      if (typeof applicationId !== "string") return { ok: false, error: "The payload has no application_id." };
      const { data, error } = await admin
        .from("applications")
        .select(
          `created_at, best_posts, why,
           applicant:profiles!applications_applicant_fkey (display_name, email, x_handle, followers, avg_views, niches, country, tiktok_url, youtube_url, instagram_url, linkedin_url),
           referrer:profiles!applications_referred_by_fkey (display_name, x_handle)`,
        )
        .eq("id", applicationId)
        .maybeSingle();
      if (error) return { ok: false, error: `Couldn't load the application: ${error.code ?? error.message}` };
      const applicant = first(data?.applicant) as ApplicantRow | null;
      if (!data || !applicant) return { ok: false, error: "The application no longer exists." };
      const referrer = first(data.referrer) as { display_name: string; x_handle: string | null } | null;
      const rendered = applicationReceivedEmail(
        {
          createdAt: data.created_at,
          bestPosts: data.best_posts,
          why: data.why,
          applicant: {
            displayName: applicant.display_name,
            email: applicant.email,
            xHandle: applicant.x_handle,
            followers: applicant.followers,
            avgViews: applicant.avg_views,
            niches: applicant.niches ?? [],
            country: applicant.country,
            tiktokUrl: applicant.tiktok_url,
            youtubeUrl: applicant.youtube_url,
            instagramUrl: applicant.instagram_url,
            linkedinUrl: applicant.linkedin_url,
          },
          referrer: referrer ? { displayName: referrer.display_name, xHandle: referrer.x_handle } : null,
        },
        { siteUrl: siteConfig.url },
      );
      // Replies go straight to the applicant.
      return { ok: true, email: { ...rendered, ...(applicant.email ? { replyTo: applicant.email } : {}) } };
    }
    case "application_approved":
    case "application_rejected":
    case "payout_details_changed": {
      const profileId = row.payload?.profile_id;
      if (typeof profileId !== "string") return { ok: false, error: "The payload has no profile_id." };
      const { data, error } = await admin
        .from("profiles")
        .select("display_name, referral_code")
        .eq("id", profileId)
        .maybeSingle();
      if (error) return { ok: false, error: `Couldn't load the profile: ${error.code ?? error.message}` };
      if (!data) return { ok: false, error: "The profile no longer exists." };
      const options = { siteUrl: siteConfig.url, contactEmail: siteConfig.contactEmail };
      const rendered =
        row.template === "application_approved"
          ? applicationApprovedEmail(
              { displayName: data.display_name, referralCode: data.referral_code, viaInvite: typeof row.payload?.invite_id === "string" },
              options,
            )
          : row.template === "application_rejected"
            ? applicationRejectedEmail({ displayName: data.display_name }, options)
            : payoutDetailsChangedEmail(
                { displayName: data.display_name, summary: String(row.payload?.summary ?? "New details") },
                options,
              );
      // Replies reach the agency's contact address.
      const replyTo = siteConfig.contactEmail.trim();
      return { ok: true, email: { ...rendered, ...(replyTo ? { replyTo } : {}) } };
    }
    default:
      return { ok: false, error: `Unknown template "${row.template}".` };
  }
}

type ApplicantRow = {
  display_name: string;
  email: string | null;
  x_handle: string | null;
  followers: number | null;
  avg_views: number | null;
  niches: string[] | null;
  country: string | null;
  tiktok_url: string | null;
  youtube_url: string | null;
  instagram_url: string | null;
  linkedin_url: string | null;
};

/** PostgREST returns an embedded row as an object, or a one-item list depending on the relation. */
function first<T>(value: T | T[] | null | undefined): T | null {
  return (Array.isArray(value) ? value[0] : value) ?? null;
}
