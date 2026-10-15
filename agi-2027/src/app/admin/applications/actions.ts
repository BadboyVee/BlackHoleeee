"use server";

import { refresh } from "next/cache";

import { FORM_PROBLEM, NOT_CONNECTED, reviewErrorMessage } from "@/lib/creators/messages";
import { issuesByPath, reviewSchema, type CreatorFormState } from "@/lib/creators/schemas";
import { deliverSoon } from "@/lib/outbox/deliver-soon";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Approve or reject an application, with private notes. The database checks
 * the caller is staff and that nobody decided it already, then emails the
 * applicant.
 */
export async function reviewApplication(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const id = String(formData.get("id") ?? "");
  const parsed = reviewSchema.safeParse({ decision: formData.get("decision"), note: String(formData.get("note") ?? "") });
  if (!UUID.test(id) || !parsed.success) {
    return { status: "error", message: FORM_PROBLEM, fieldErrors: parsed.success ? {} : issuesByPath(parsed.error.issues) };
  }
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const supabase = await createClient();
  const { data, error } = await supabase.rpc("review_application", {
    p_application: id,
    p_decision: parsed.data.decision,
    p_note: parsed.data.note,
  });
  if (error) {
    if (error.code === "P0409") refresh();
    else console.error(`[review] review_application failed: ${error.code ?? "no code"}`);
    return { status: "error", message: reviewErrorMessage(error) };
  }
  deliverSoon(data, "review");
  refresh();
  return {
    status: "saved",
    message: parsed.data.decision === "approve" ? "Approved. They'll get a welcome email." : "Rejected. They'll get a kind note.",
  };
}
