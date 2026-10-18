import type { NextRequest } from "next/server";

import { landingRedirect, landSignedIn } from "@/lib/auth/landing";
import { safeNextPath } from "@/lib/auth/routes";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

/**
 * Where Google and Supabase's standard email links come back to, with a
 * one-time code to swap for a session. The swap needs a secret the browser
 * kept when the sign in started, so it only works in that same browser.
 *
 * When it fails: an email link has still confirmed the address (Supabase
 * did that before sending the person here), so they're asked to sign in; a
 * reset link has to be asked for again; Google can simply be tried again.
 */
export async function GET(request: NextRequest) {
  const { origin, searchParams } = request.nextUrl;
  const flow = searchParams.get("flow");
  const next = safeNextPath(searchParams.get("next"));
  const code = searchParams.get("code");

  // Supabase reports a link that expired or was used before as ?error=...&error_code=...
  const linkError = searchParams.get("error") ?? searchParams.get("error_code");
  if (!getSupabaseEnv() || !code || linkError) return landingRedirect(origin, failure(flow, Boolean(linkError)));

  const supabase = await createClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    console.error(`[auth] code exchange failed for ${flow ?? "unknown"}: ${error.code ?? "no code"}`);
    return landingRedirect(origin, failure(flow, false));
  }
  return landSignedIn(supabase, origin, { recovery: flow === "recovery", next });
}

function failure(flow: string | null, linkRejected: boolean): string {
  switch (flow) {
    case "recovery":
      return "/forgot-password?status=expired";
    case "signup":
      // A rejected link confirmed nothing. An accepted one did, even if this browser can't finish the sign in.
      return linkRejected ? "/login?error=link" : "/login?status=confirmed";
    case "google":
      return "/login?error=google";
    default:
      return "/login?error=auth";
  }
}
