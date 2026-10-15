"use server";

import { refresh } from "next/cache";

import { FORM_PROBLEM, NOT_CONNECTED, profileErrorMessage } from "@/lib/creators/messages";
import { issuesByPath, payoutSchema, profileSchema, type CreatorFormState } from "@/lib/creators/schemas";
import { deliverSoon } from "@/lib/outbox/deliver-soon";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

function text(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.slice(0, 2100) : "";
}

/**
 * The creator's own profile. Row level security limits the update to their
 * own row, and column grants to the fields they may change (never their X
 * handle, role or referral code).
 */
export async function updateProfile(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const parsed = profileSchema.safeParse({
    displayName: text(formData, "displayName"),
    tiktok: text(formData, "tiktok"),
    youtube: text(formData, "youtube"),
    instagram: text(formData, "instagram"),
    linkedin: text(formData, "linkedin"),
    niches: formData.getAll("niches").filter((value): value is string => typeof value === "string"),
    followers: text(formData, "followers"),
    avgViews: text(formData, "avgViews"),
    country: text(formData, "country"),
    bio: text(formData, "bio"),
    ratePerPost: text(formData, "ratePerPost"),
    rateCurrency: text(formData, "rateCurrency") || undefined,
  });
  if (!parsed.success) return { status: "error", message: FORM_PROBLEM, fieldErrors: issuesByPath(parsed.error.issues) };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const supabase = await createClient();
  const { data: session } = await supabase.auth.getClaims();
  const userId = session?.claims?.sub;
  if (typeof userId !== "string") return { status: "error", message: "Your sign-in has expired. Sign in again." };

  const values = parsed.data;
  const { error } = await supabase
    .from("profiles")
    .update({
      display_name: values.displayName,
      tiktok_url: values.tiktok ?? null,
      youtube_url: values.youtube ?? null,
      instagram_url: values.instagram ?? null,
      linkedin_url: values.linkedin ?? null,
      niches: values.niches,
      followers: values.followers,
      avg_views: values.avgViews,
      country: values.country,
      bio: values.bio,
      rate_per_post: values.ratePerPost ?? null,
      rate_currency: values.rateCurrency ?? null,
    })
    .eq("id", userId);
  if (error) {
    console.error(`[profile] update failed: ${error.code ?? "no code"}`);
    return { status: "error", message: profileErrorMessage(error) };
  }
  refresh();
  return { status: "saved", message: "Profile saved." };
}

/**
 * Where to pay them. Goes through set_payout_details, which keeps only the
 * chosen method's fields, logs the change and emails the creator, so nobody
 * can swap the details quietly.
 */
export async function savePayoutDetails(_prev: CreatorFormState, formData: FormData): Promise<CreatorFormState> {
  const method = text(formData, "method");
  const parsed = payoutSchema.safeParse(
    method === "crypto"
      ? { method, asset: text(formData, "asset"), network: text(formData, "network"), wallet: text(formData, "wallet") }
      : method === "bank"
        ? {
            method,
            bankCountry: text(formData, "bankCountry"),
            bankName: text(formData, "bankName"),
            accountName: text(formData, "accountName"),
            accountNumber: text(formData, "accountNumber"),
            bankCode: text(formData, "bankCode") || undefined,
          }
        : { method, otherDetails: text(formData, "otherDetails") },
  );
  if (!parsed.success) return { status: "error", message: FORM_PROBLEM, fieldErrors: issuesByPath(parsed.error.issues) };
  if (!getSupabaseEnv()) return { status: "error", message: NOT_CONNECTED };

  const details = parsed.data;
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("set_payout_details", {
    p_method: details.method,
    p_crypto_asset: details.method === "crypto" ? details.asset : null,
    p_crypto_network: details.method === "crypto" ? details.network : null,
    p_wallet_address: details.method === "crypto" ? details.wallet : null,
    p_bank_country: details.method === "bank" ? details.bankCountry : null,
    p_bank_name: details.method === "bank" ? details.bankName : null,
    p_account_name: details.method === "bank" ? details.accountName : null,
    p_account_number: details.method === "bank" ? details.accountNumber : null,
    p_bank_code: details.method === "bank" ? (details.bankCode ?? null) : null,
    p_other_details: details.method === "other" ? details.otherDetails : null,
  });
  if (error) {
    console.error(`[profile] set_payout_details failed: ${error.code ?? "no code"}`);
    return { status: "error", message: profileErrorMessage(error) };
  }
  deliverSoon(data, "payout");
  refresh();
  return { status: "saved", message: "Saved. We've emailed you to confirm the change." };
}
