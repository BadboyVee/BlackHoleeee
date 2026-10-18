import type { EmailOtpType } from "@supabase/supabase-js";
import type { NextRequest } from "next/server";

import { landingRedirect, landSignedIn } from "@/lib/auth/landing";
import { nextFromUrlOrPath } from "@/lib/auth/routes";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

/** The email link types this route accepts. */
const TYPES: readonly EmailOtpType[] = ["signup", "email", "recovery", "invite", "magiclink", "email_change"];

/**
 * Where the project's own email templates send people (supabase/templates):
 * the link carries a token hash that's checked here, so it works in any
 * browser, unlike the standard links (see /auth/callback).
 */
export async function GET(request: NextRequest) {
  const { origin, searchParams } = request.nextUrl;
  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  const recovery = type === "recovery";

  if (!getSupabaseEnv() || !tokenHash || !type || !TYPES.includes(type)) {
    return landingRedirect(origin, "/login?error=link");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.verifyOtp({ type, token_hash: tokenHash });
  if (error) {
    console.error(`[auth] email link rejected for ${type}: ${error.code ?? "no code"}`);
    return landingRedirect(origin, recovery ? "/forgot-password?status=expired" : "/login?error=link");
  }
  return landSignedIn(supabase, origin, { recovery, next: nextFromUrlOrPath(searchParams.get("next"), origin) });
}
