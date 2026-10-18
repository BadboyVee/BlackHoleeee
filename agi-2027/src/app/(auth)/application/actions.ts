"use server";

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import {
  applicationErrorMessage,
  FORM_PROBLEM,
  INVITE_AFTER_REJECTION,
  inviteStateFromError,
  inviteStateMessage,
  NOT_CONNECTED,
} from "@/lib/creators/messages";
import { parseInviteCode } from "@/lib/creators/display";
import { applicationSchema, issuesByPath, type CreatorFormState } from "@/lib/creators/schemas";
import { deliverSoon } from "@/lib/outbox/deliver-soon";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

/*
 * The applicant's side: sending the application, and using an invite link.
 * Both run as the signed-in person, so the database functions check who
 * they are (applicants only) themselves.
 */

function text(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.slice(0, 2100) : "";
}

function texts(formData: FormData, name: string): string[] {
  return formData
    .getAll(name)
    .filter((value): value is string => typeof value === "string")
    .map((value) => value.slice(0, 2100));
}

export async function submitApplication(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  // One field per post, named like their errors: bestPosts.0 to bestPosts.2.
  const posts = [0, 1, 2].map((index) => text(formData, `bestPosts.${index}`));
  const parsed = applicationSchema.safeParse({
    displayName: text(formData, "displayName"),
    xHandle: text(formData, "xHandle"),
    tiktok: text(formData, "tiktok"),
    youtube: text(formData, "youtube"),
    instagram: text(formData, "instagram"),
    linkedin: text(formData, "linkedin"),
    niches: texts(formData, "niches"),
    followers: text(formData, "followers"),
    avgViews: text(formData, "avgViews"),
    country: text(formData, "country"),
    bestPosts: [posts[0], posts[1], posts[2]],
    why: text(formData, "why"),
    referralCode: text(formData, "referralCode"),
  });
  if (!parsed.success) return { status: "error", message: FORM_PROBLEM, fieldErrors: issuesByPath(parsed.error.issues) };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const answers = parsed.data;
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("submit_application", {
    p_display_name: answers.displayName,
    p_x_handle: answers.xHandle,
    p_tiktok_url: answers.tiktok ?? null,
    p_youtube_url: answers.youtube ?? null,
    p_instagram_url: answers.instagram ?? null,
    p_linkedin_url: answers.linkedin ?? null,
    p_niches: answers.niches,
    p_followers: answers.followers,
    p_avg_views: answers.avgViews,
    p_country: answers.country,
    p_best_posts: answers.bestPosts,
    p_why: answers.why,
    p_referral_code: answers.referralCode ?? null,
  });
  if (error) {
    const problem = applicationErrorMessage(error);
    // Already applied: show them where it stands.
    if (error.code === "P0409") refresh();
    else console.error(`[application] submit failed: ${error.code ?? "no code"}`);
    return {
      status: "error",
      message: problem.message,
      ...(problem.field ? { fieldErrors: { [problem.field]: problem.message } } : {}),
    };
  }

  const row = (Array.isArray(data) ? data[0] : data) as { outbox_id?: unknown } | null;
  deliverSoon(row?.outbox_id, "application");
  refresh();
  return { status: "saved" };
}

/** Uses an invite link: approved on the spot, then straight to the creator app. */
export async function redeemInvite(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const code = parseInviteCode(text(formData, "code"));
  if (!code) return { status: "error", message: inviteStateMessage("unknown") };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const supabase = await createClient();
  const { data: session } = await supabase.auth.getClaims();
  if (!session?.claims?.sub) redirect(`/login?next=${encodeURIComponent(`/invite/${code}`)}`);

  const { data, error } = await supabase.rpc("redeem_invite", { p_code: code });
  if (error) {
    const state = inviteStateFromError(error);
    if (state) return { status: "error", message: inviteStateMessage(state) };
    if (error.code === "42501") return { status: "error", message: "This account is already in. Head to your dashboard." };
    if (error.code === "P0409") return { status: "error", message: INVITE_AFTER_REJECTION };
    console.error(`[invite] redeem failed: ${error.code ?? "no code"}`);
    return { status: "error", message: "We couldn't use that invite just now. Try again in a minute." };
  }
  deliverSoon(data, "invite");
  redirect("/dashboard");
}
