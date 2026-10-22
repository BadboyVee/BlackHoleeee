import "server-only";

import { unstable_rethrow } from "next/navigation";

import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

/*
 * Reads for the onboarding screens. Every read uses the signed-in person's
 * session, so row level security decides what comes back: applicants see
 * their own application, staff see them all, only the admin sees invites and
 * other people's payout details. Each reads cookies: call them inside
 * <Suspense>. They return null when Supabase isn't set up yet.
 */

export type ApplicationStatus = "submitted" | "approved" | "rejected";

export type MyApplication = { id: string; status: ApplicationStatus; createdAt: string; reviewedAt: string | null };

export type CreatorProfile = {
  id: string;
  email: string | null;
  role: string;
  displayName: string;
  avatarUrl: string | null;
  xHandle: string | null;
  tiktokUrl: string | null;
  youtubeUrl: string | null;
  instagramUrl: string | null;
  linkedinUrl: string | null;
  niches: string[];
  followers: number | null;
  avgViews: number | null;
  country: string | null;
  bio: string;
  ratePerPost: string | null;
  rateCurrency: string | null;
  referralCode: string | null;
};

export type PayoutDetails = {
  method: "crypto" | "bank" | "other";
  cryptoAsset: string | null;
  cryptoNetwork: string | null;
  walletAddress: string | null;
  bankCountry: string | null;
  bankName: string | null;
  accountName: string | null;
  accountNumber: string | null;
  bankCode: string | null;
  otherDetails: string | null;
  updatedAt: string;
};

export type ApplicationRow = {
  id: string;
  status: ApplicationStatus;
  bestPosts: string[] | null;
  why: string | null;
  reviewNote: string;
  createdAt: string;
  reviewedAt: string | null;
  invited: boolean;
  applicant: Omit<CreatorProfile, "role" | "bio" | "ratePerPost" | "rateCurrency" | "referralCode">;
  referrer: { displayName: string; xHandle: string | null } | null;
  reviewer: { displayName: string } | null;
};

/** Someone who made an account but hasn't sent the application form. */
export type SignupRow = {
  id: string;
  email: string | null;
  displayName: string;
  createdAt: string;
};

export type InviteRow = {
  id: string;
  code: string;
  label: string;
  maxUses: number | null;
  uses: number;
  expiresAt: string | null;
  revokedAt: string | null;
  createdAt: string;
};

const PROFILE_COLUMNS =
  "id, email, role, display_name, avatar_url, x_handle, tiktok_url, youtube_url, instagram_url, linkedin_url, niches, followers, avg_views, country, bio, rate_per_post, rate_currency, referral_code";

type ProfileRow = {
  id: string;
  email: string | null;
  role: string;
  display_name: string;
  avatar_url: string | null;
  x_handle: string | null;
  tiktok_url: string | null;
  youtube_url: string | null;
  instagram_url: string | null;
  linkedin_url: string | null;
  niches: string[] | null;
  followers: number | null;
  avg_views: number | null;
  country: string | null;
  bio: string | null;
  rate_per_post: string | number | null;
  rate_currency: string | null;
  referral_code: string | null;
};

function toProfile(row: ProfileRow): CreatorProfile {
  return {
    id: row.id,
    email: row.email,
    role: row.role,
    displayName: row.display_name,
    avatarUrl: row.avatar_url,
    xHandle: row.x_handle,
    tiktokUrl: row.tiktok_url,
    youtubeUrl: row.youtube_url,
    instagramUrl: row.instagram_url,
    linkedinUrl: row.linkedin_url,
    niches: row.niches ?? [],
    followers: row.followers,
    avgViews: row.avg_views,
    country: row.country,
    bio: row.bio ?? "",
    ratePerPost: row.rate_per_post === null ? null : String(row.rate_per_post),
    rateCurrency: row.rate_currency,
    referralCode: row.referral_code,
  };
}

/** The Supabase client and the caller's id, or null when Supabase isn't set up or nobody is signed in. */
async function session() {
  if (!getSupabaseEnv()) return null;
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const userId = data?.claims?.sub;
  return typeof userId === "string" ? { supabase, userId } : null;
}

function logFailure(what: string, error: unknown) {
  unstable_rethrow(error);
  console.error(`[creators] reading ${what} failed: ${error instanceof Error ? error.name : "unknown error"}`);
}

export async function getMyApplication(): Promise<MyApplication | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data } = await current.supabase
      .from("applications")
      .select("id, status, created_at, reviewed_at")
      .eq("applicant", current.userId)
      .maybeSingle();
    return data ? { id: data.id, status: data.status, createdAt: data.created_at, reviewedAt: data.reviewed_at } : null;
  } catch (error) {
    logFailure("the application", error);
    return null;
  }
}

export async function getMyProfile(): Promise<CreatorProfile | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data } = await current.supabase.from("profiles").select(PROFILE_COLUMNS).eq("id", current.userId).maybeSingle();
    return data ? toProfile(data as ProfileRow) : null;
  } catch (error) {
    logFailure("the profile", error);
    return null;
  }
}

export async function getMyPayoutDetails(): Promise<PayoutDetails | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data } = await current.supabase
      .from("payout_details")
      .select(
        "method, crypto_asset, crypto_network, wallet_address, bank_country, bank_name, account_name, account_number, bank_code, other_details, updated_at",
      )
      .eq("profile_id", current.userId)
      .maybeSingle();
    if (!data) return null;
    return {
      method: data.method,
      cryptoAsset: data.crypto_asset,
      cryptoNetwork: data.crypto_network,
      walletAddress: data.wallet_address,
      bankCountry: data.bank_country,
      bankName: data.bank_name,
      accountName: data.account_name,
      accountNumber: data.account_number,
      bankCode: data.bank_code,
      otherDetails: data.other_details,
      updatedAt: data.updated_at,
    };
  } catch (error) {
    logFailure("payout details", error);
    return null;
  }
}

export async function getMyReferrals(): Promise<{ applied: number; approved: number } | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data } = await current.supabase.rpc("my_referrals");
    const row = (Array.isArray(data) ? data[0] : data) as { applied?: number; approved?: number } | null;
    return { applied: row?.applied ?? 0, approved: row?.approved ?? 0 };
  } catch (error) {
    logFailure("referrals", error);
    return null;
  }
}

/** Every application, newest first, with who sent it, who referred them and who reviewed it. Staff only (RLS). */
export async function listApplications(): Promise<ApplicationRow[] | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data, error } = await current.supabase
      .from("applications")
      .select(
        `id, status, best_posts, why, created_at, reviewed_at, invite_id,
         applicant:profiles!applications_applicant_fkey (${PROFILE_COLUMNS}),
         referrer:profiles!applications_referred_by_fkey (display_name, x_handle),
         review:application_reviews (note, reviewer:profiles!application_reviews_reviewed_by_fkey (display_name))`,
      )
      .order("created_at", { ascending: false })
      .limit(500);
    if (error) {
      console.error(`[creators] listing applications failed: ${error.code ?? "no code"}`);
      return [];
    }
    return (data ?? []).flatMap((row) => {
      const applicant = (Array.isArray(row.applicant) ? row.applicant[0] : row.applicant) as ProfileRow | null;
      if (!applicant) return [];
      const referrer = (Array.isArray(row.referrer) ? row.referrer[0] : row.referrer) as
        | { display_name: string; x_handle: string | null }
        | null;
      // The decision and private note live in a staff-only table of their own (one per application).
      const review = (Array.isArray(row.review) ? row.review[0] : row.review) as
        | { note: string; reviewer: { display_name: string } | { display_name: string }[] | null }
        | null
        | undefined;
      const reviewer = review ? (Array.isArray(review.reviewer) ? review.reviewer[0] : review.reviewer) : null;
      const profile = toProfile(applicant);
      return [
        {
          id: row.id,
          status: row.status,
          bestPosts: row.best_posts,
          why: row.why,
          reviewNote: review?.note ?? "",
          createdAt: row.created_at,
          reviewedAt: row.reviewed_at,
          invited: row.invite_id !== null,
          applicant: {
            id: profile.id,
            email: profile.email,
            displayName: profile.displayName,
            avatarUrl: profile.avatarUrl,
            xHandle: profile.xHandle,
            tiktokUrl: profile.tiktokUrl,
            youtubeUrl: profile.youtubeUrl,
            instagramUrl: profile.instagramUrl,
            linkedinUrl: profile.linkedinUrl,
            niches: profile.niches,
            followers: profile.followers,
            avgViews: profile.avgViews,
            country: profile.country,
          },
          referrer: referrer ? { displayName: referrer.display_name, xHandle: referrer.x_handle } : null,
          reviewer: reviewer ? { displayName: reviewer.display_name } : null,
        },
      ];
    });
  } catch (error) {
    logFailure("applications", error);
    return [];
  }
}

/**
 * Active applicants with no application yet, newest first: they signed up but
 * never sent the form. Staff only (RLS). The application is embedded rather
 * than filtered by the database, so this reads the same way as listApplications.
 */
export async function listSignupsWithoutApplication(): Promise<SignupRow[] | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data, error } = await current.supabase
      .from("profiles")
      .select("id, email, display_name, created_at, application:applications!applications_applicant_fkey (id)")
      .eq("role", "applicant")
      .eq("status", "active")
      .order("created_at", { ascending: false })
      .limit(500);
    if (error) {
      console.error(`[creators] listing sign ups failed: ${error.code ?? "no code"}`);
      return [];
    }
    return (data ?? []).flatMap((row) => {
      // One application per person, so this is an object or null (an array on older PostgREST).
      const application = Array.isArray(row.application) ? row.application[0] : row.application;
      if (application) return [];
      return [{ id: row.id, email: row.email, displayName: row.display_name, createdAt: row.created_at }];
    });
  } catch (error) {
    logFailure("sign ups", error);
    return [];
  }
}

/** Every invite link, newest first. Admin only (RLS). */
export async function listInvites(): Promise<InviteRow[] | null> {
  try {
    const current = await session();
    if (!current) return null;
    const { data, error } = await current.supabase
      .from("invites")
      .select("id, code, label, max_uses, uses, expires_at, revoked_at, created_at")
      .order("created_at", { ascending: false })
      .limit(500);
    if (error) {
      console.error(`[creators] listing invites failed: ${error.code ?? "no code"}`);
      return [];
    }
    return (data ?? []).map((row) => ({
      id: row.id,
      code: row.code,
      label: row.label,
      maxUses: row.max_uses,
      uses: row.uses,
      expiresAt: row.expires_at,
      revokedAt: row.revoked_at,
      createdAt: row.created_at,
    }));
  } catch (error) {
    logFailure("invites", error);
    return [];
  }
}

/** Where an invite code stands, for the invite page. Anyone can ask. */
export async function inviteState(code: string): Promise<"valid" | "revoked" | "expired" | "used_up" | "unknown" | null> {
  if (!getSupabaseEnv()) return null;
  try {
    const supabase = await createClient();
    const { data, error } = await supabase.rpc("invite_preview", { p_code: code });
    if (error) {
      console.error(`[creators] checking an invite failed: ${error.code ?? "no code"}`);
      return null;
    }
    return data as "valid" | "revoked" | "expired" | "used_up" | "unknown";
  } catch (error) {
    logFailure("an invite", error);
    return null;
  }
}
