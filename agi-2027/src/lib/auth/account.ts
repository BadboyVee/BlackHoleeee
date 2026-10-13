import "server-only";

import { unstable_rethrow } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { getSupabaseEnv } from "@/lib/supabase/env";

import { toAccount, type Account } from "./account-display";

/**
 * The signed-in person, or null when nobody is signed in or Supabase isn't
 * configured (preview links run on demo data then). Reads the session
 * cookie, so call it inside a <Suspense> boundary. The role comes from the
 * database, never from the token, so it's always current.
 */
export async function getAccount(): Promise<Account | null> {
  if (!getSupabaseEnv()) return null;
  try {
    const supabase = await createClient();
    const { data } = await supabase.auth.getClaims();
    const claims = data?.claims;
    if (!claims?.sub) return null;
    const { data: profile } = await supabase
      .from("profiles")
      .select("role, status, display_name, avatar_url, email")
      .eq("id", claims.sub)
      .maybeSingle();
    return toAccount(claims.sub, profile, typeof claims.email === "string" ? claims.email : undefined);
  } catch (error) {
    // Next.js interrupts request-time reads while prerendering; those must reach Next.js, not this log.
    unstable_rethrow(error);
    console.error(`[auth] reading the account failed: ${error instanceof Error ? error.name : "unknown error"}`);
    return null;
  }
}
