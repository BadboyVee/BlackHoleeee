import "server-only";

import { createHash, createHmac } from "node:crypto";

import { createAdminClient } from "@/lib/supabase/admin";
import { getSupabaseEnv } from "@/lib/supabase/env";

/*
 * Rate limits for public forms. Buckets hold a salted SHA-256 of what's being
 * limited (an IP or an email address), never the value itself. The limits
 * live in the database (public.hit_rate_limit and public.submit_lead).
 */

/** Used only when RATE_LIMIT_SALT and SUPABASE_SECRET_KEY are both missing, so local development still rate limits. */
const FALLBACK_SALT = "agi-2027-dev-rate-limit-salt";
let warnedAboutSalt = false;

/**
 * RATE_LIMIT_SALT when it's set. Otherwise a value made from the Supabase
 * secret key, which the site needs to save anything at all, so the salt is
 * still secret, as the privacy page says. The key itself never goes into the
 * hash. The built-in salt is only for local development without either.
 */
function rateLimitSalt(): string {
  const salt = process.env.RATE_LIMIT_SALT;
  if (salt) return salt;
  const secretKey = process.env.SUPABASE_SECRET_KEY;
  if (secretKey) return createHmac("sha256", secretKey).update("agi-2027 rate limit salt").digest("hex");
  if (!warnedAboutSalt) {
    warnedAboutSalt = true;
    console.warn("[rate-limit] Neither RATE_LIMIT_SALT nor SUPABASE_SECRET_KEY is set. Using the built-in development salt.");
  }
  return FALLBACK_SALT;
}

/** A salted SHA-256 of an IP or email address, so the rate limit table never holds the real thing. */
export function rateKey(value: string): string {
  return createHash("sha256").update(rateLimitSalt() + value).digest("hex");
}

/** The limits public.hit_rate_limit knows, each per clock hour. */
export type RateLimitKind = "sign_in_ip" | "sign_in_email" | "sign_up_ip" | "auth_email_ip" | "auth_email_address";

/**
 * Counts one try against a limit and says whether it may go ahead. `value`
 * is hashed first. Fails open: if the database can't be reached, Supabase
 * Auth's own limits still apply, and nobody is locked out by an outage.
 */
export async function hitRateLimit(kind: RateLimitKind, value: string): Promise<boolean> {
  if (!getSupabaseEnv() || !process.env.SUPABASE_SECRET_KEY) return true;
  try {
    const { data, error } = await createAdminClient().rpc("hit_rate_limit", { p_kind: kind, p_key: rateKey(value) });
    if (error) {
      console.error(`[rate-limit] hit_rate_limit failed for ${kind}: ${error.code ?? "no code"}`);
      return true;
    }
    return data !== false;
  } catch (error) {
    console.error(`[rate-limit] hit_rate_limit threw for ${kind}: ${error instanceof Error ? error.name : "unknown error"}`);
    return true;
  }
}
