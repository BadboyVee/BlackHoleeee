import "server-only";

import { NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

import { destinationFor } from "./routes";
import { currentRole } from "./server";

/*
 * Shared by /auth/callback and /auth/confirm, the two places Supabase sends
 * people back to.
 */

/** A redirect that sets auth cookies, so no CDN may ever cache it. */
export function landingRedirect(origin: string, to: string): NextResponse {
  const response = NextResponse.redirect(new URL(to, origin), 307);
  response.headers.set("Cache-Control", "private, no-cache, no-store, must-revalidate, max-age=0");
  return response;
}

/** Signed in: on to where they were going, or their role's home. A reset link goes to the new password form. */
export async function landSignedIn(
  supabase: Awaited<ReturnType<typeof createClient>>,
  origin: string,
  { recovery, next }: { recovery: boolean; next: string | null },
): Promise<NextResponse> {
  if (recovery) return landingRedirect(origin, "/reset-password");
  return landingRedirect(origin, destinationFor(await currentRole(supabase), next));
}
