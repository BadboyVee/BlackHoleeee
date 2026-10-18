import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

import {
  accessFor,
  areaFor,
  isPrivateArea,
  parseRoleClaim,
  signedOutRedirect,
  type Decision,
  type RoleClaim,
} from "@/lib/auth/routes";
import { isLiveSite } from "@/lib/deploy";
import { getSupabaseEnv } from "@/lib/supabase/env";

/**
 * Runs before every private page, the sign-in pages and invite links:
 *
 * 1. Refreshes the Supabase session when its token is about to run out, so
 *    Server Components (which can't set cookies) always see a fresh one.
 * 2. Sends signed-out visitors to /login, remembering where they were going.
 * 3. Sends signed-in people to the right app for their role
 *    (src/lib/auth/routes.ts has the rules).
 *
 * The role comes from the token's user_role claim, which the access token
 * hook adds. A claim can be up to an hour old, so before turning anyone away
 * the database gets the last word. Data itself is protected by RLS; this
 * only decides which screens people see. Server Actions check the session
 * themselves too, never relying on this.
 *
 * Without Supabase settings (a preview link before setup, or a laptop) there
 * are no accounts to check: the demo apps stay open, except on the live site.
 */
export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const area = areaFor(pathname);
  if (area === null) return NextResponse.next();

  const env = getSupabaseEnv();
  if (!env) {
    return isPrivateArea(area) && isLiveSite() ? redirectTo(request, "/") : NextResponse.next();
  }

  let response = NextResponse.next({ request });
  const supabase = createServerClient(env.url, env.publishableKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet, headers) {
        for (const { name, value } of cookiesToSet) request.cookies.set(name, value);
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) response.cookies.set(name, value, options);
        // Responses that set auth cookies must never be cached by a CDN.
        for (const [key, value] of Object.entries(headers)) response.headers.set(key, value);
      },
    },
  });

  // Checks the token, refreshing it first if it's about to run out. Keep this the first call on the client.
  let claims: { sub?: unknown; user_role?: unknown } | null = null;
  try {
    const { data } = await supabase.auth.getClaims();
    claims = data?.claims ?? null;
  } catch (error) {
    console.error(`[proxy] checking the session failed: ${error instanceof Error ? error.name : "unknown error"}`);
  }

  // Invite links are for everyone: they only needed the session refreshed.
  if (area === "open") return response;

  const userId = typeof claims?.sub === "string" ? claims.sub : null;
  if (!userId) {
    const to = signedOutRedirect(pathname, search);
    return to ? redirectWith(response, request, to) : response;
  }

  const next = request.nextUrl.searchParams.get("next");
  const claimed = parseRoleClaim(claims?.user_role);
  let decision: Decision | null = claimed ? accessFor(pathname, claimed, next) : null;

  // Ask the database when the claim is missing (hook not on yet), when it would turn someone
  // away (they may have just been promoted), and on the application page (applicants move on).
  if (!decision || decision.kind === "redirect" || area === "applicant") {
    const fresh = await roleFromDatabase(supabase, userId);
    if (fresh) decision = accessFor(pathname, fresh, next);
    else if (!decision) decision = isPrivateArea(area) ? { kind: "redirect", to: "/login?error=auth" } : { kind: "allow" };
  }

  return decision.kind === "allow" ? response : redirectWith(response, request, decision.to);
}

/** The account's current role, "none" when it isn't active or has no profile, or null when the database didn't answer. */
async function roleFromDatabase(supabase: SupabaseClient, userId: string): Promise<RoleClaim | null> {
  try {
    const { data, error } = await supabase.from("profiles").select("role, status").eq("id", userId).maybeSingle();
    if (error) {
      console.error(`[proxy] reading the role failed: ${error.code ?? "no code"}`);
      return null;
    }
    if (!data || data.status !== "active") return "none";
    return parseRoleClaim(data.role) ?? "none";
  } catch (error) {
    console.error(`[proxy] reading the role threw: ${error instanceof Error ? error.name : "unknown error"}`);
    return null;
  }
}

function redirectTo(request: NextRequest, to: string) {
  return NextResponse.redirect(new URL(to, request.url), 307);
}

/** A redirect that keeps any refreshed session cookies, and the no-cache headers that come with them. */
function redirectWith(response: NextResponse, request: NextRequest, to: string) {
  const redirect = redirectTo(request, to);
  for (const cookie of response.cookies.getAll()) redirect.cookies.set(cookie);
  for (const header of ["cache-control", "expires", "pragma"]) {
    const value = response.headers.get(header);
    if (value) redirect.headers.set(header, value);
  }
  return redirect;
}

export const config = {
  matcher: [
    "/admin/:path*",
    "/dashboard/:path*",
    "/application/:path*",
    "/styleguide/:path*",
    "/login",
    "/signup",
    "/reset-password",
    "/invite/:path*",
  ],
};
