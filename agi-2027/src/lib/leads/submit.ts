import "server-only";

import { createAdminClient } from "@/lib/supabase/admin";
import { getSupabaseEnv } from "@/lib/supabase/env";

import type { Booking, LeadSource } from "./booking";
import { classifySubmitError, type SubmitLeadResult } from "./errors";

/** True when the server can write leads: the Supabase URL and keys plus the secret key are set. */
export function leadStoreConfigured(): boolean {
  return Boolean(getSupabaseEnv() && process.env.SUPABASE_SECRET_KEY);
}

/**
 * Saves a booking through public.submit_lead, which rate limits the caller,
 * inserts the lead, queues the owner's email in the outbox and writes the
 * activity log in one transaction. Never throws: the result says what
 * happened, and the caller picks the words.
 *
 * `rateKey` is a salted hash of the visitor's IP, never the IP itself.
 */
export async function submitLead(
  booking: Booking,
  { source, rateKey }: { source: LeadSource; rateKey: string },
): Promise<SubmitLeadResult> {
  if (!leadStoreConfigured()) return { ok: false, reason: "not_configured" };

  try {
    const { data, error } = await createAdminClient().rpc("submit_lead", {
      p_name: booking.name,
      p_email: booking.email,
      p_company: booking.company,
      p_website: booking.website ?? null,
      p_x_handle: booking.xHandle ?? null,
      p_launching: booking.launching,
      p_launch_date: booking.launchDate ?? null,
      p_budget: booking.budget,
      p_message: booking.message ?? null,
      p_source: source,
      p_rate_key: rateKey,
    });

    if (error) {
      const reason = classifySubmitError(error);
      // Code and message only: PostgREST's `details` can quote the row, which holds personal data.
      if (reason !== "rate_limited") {
        console.error(`[leads] submit_lead failed: ${error.code ?? "no code"} ${truncate(error.message)}`);
      }
      return { ok: false, reason, code: error.code };
    }

    const row = (Array.isArray(data) ? data[0] : data) as { lead_id?: unknown; outbox_id?: unknown } | null;
    if (typeof row?.lead_id !== "string" || typeof row?.outbox_id !== "string") {
      console.error("[leads] submit_lead returned no lead id");
      return { ok: false, reason: "failed" };
    }
    return { ok: true, leadId: row.lead_id, outboxId: row.outbox_id };
  } catch (error) {
    // Network failures and the like. The error's name is enough to start looking.
    console.error(`[leads] submit_lead threw: ${error instanceof Error ? error.name : "unknown error"}`);
    return { ok: false, reason: "failed" };
  }
}

function truncate(text: string | undefined, max = 200): string {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max)}...` : text;
}
