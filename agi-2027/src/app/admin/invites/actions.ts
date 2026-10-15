"use server";

import { refresh } from "next/cache";

import { adminOnlyMessage, FORM_PROBLEM, NOT_CONNECTED } from "@/lib/creators/messages";
import { INVITE_EXPIRY, inviteSchema, issuesByPath, type CreatorFormState } from "@/lib/creators/schemas";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const DAY_MS = 24 * 60 * 60 * 1000;

/** A new invite link. Admin only: the database checks. */
export async function createInvite(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const parsed = inviteSchema.safeParse({
    label: String(formData.get("label") ?? ""),
    maxUses: String(formData.get("maxUses") ?? ""),
    expiresIn: formData.get("expiresIn"),
  });
  if (!parsed.success) return { status: "error", message: FORM_PROBLEM, fieldErrors: issuesByPath(parsed.error.issues) };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const days = INVITE_EXPIRY.find((option) => option.value === parsed.data.expiresIn)?.days ?? null;
  const supabase = await createClient();
  const { error } = await supabase.rpc("create_invite", {
    p_label: parsed.data.label,
    p_max_uses: parsed.data.maxUses ?? null,
    p_expires_at: days === null ? null : new Date(Date.now() + days * DAY_MS).toISOString(),
  });
  if (error) {
    console.error(`[invites] create_invite failed: ${error.code ?? "no code"}`);
    return { status: "error", message: adminOnlyMessage(error) };
  }
  refresh();
  return { status: "saved", message: "Link created. It's at the top of the list, ready to copy." };
}

/** Switches a link off. People who already joined through it stay in. */
export async function revokeInvite(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const id = String(formData.get("id") ?? "");
  if (!UUID.test(id)) return { status: "error", message: FORM_PROBLEM };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };
  const supabase = await createClient();
  const { error } = await supabase.rpc("revoke_invite", { p_invite: id });
  if (error) {
    console.error(`[invites] revoke_invite failed: ${error.code ?? "no code"}`);
    return { status: "error", message: adminOnlyMessage(error) };
  }
  refresh();
  return { status: "saved", message: "Link switched off." };
}
