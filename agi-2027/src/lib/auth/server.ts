import "server-only";

import { headers } from "next/headers";
import type { SupabaseClient } from "@supabase/supabase-js";

import { siteConfig } from "@/lib/site";

import { parseRoleClaim, type RoleClaim } from "./routes";

/**
 * The signed-in account's role, right after signing in: the token's claim
 * when the access token hook is on (a brand new token, so it's current),
 * otherwise the database's answer.
 */
export async function currentRole(supabase: SupabaseClient): Promise<RoleClaim> {
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  const claimed = parseRoleClaim(claims?.user_role);
  if (claimed) return claimed;
  if (typeof claims?.sub !== "string") return "none";
  const { data: profile } = await supabase.from("profiles").select("role, status").eq("id", claims.sub).maybeSingle();
  return profile?.status === "active" ? (parseRoleClaim(profile.role) ?? "none") : "none";
}

/**
 * This deployment's address, for the links Supabase sends people back to
 * (Google, and the emails). It comes from the request, so preview links and
 * a custom domain each get their own. A Server Action's Origin header is
 * checked by Next.js against the host, and Supabase only redirects to
 * addresses on its allow list anyway.
 */
export async function requestOrigin(): Promise<string> {
  const list = await headers();
  const origin = list.get("origin");
  if (origin && /^https?:\/\/[^/\s]+$/i.test(origin)) return origin;
  const host = list.get("x-forwarded-host") ?? list.get("host");
  if (host && /^[a-z0-9.:[\]-]+$/i.test(host)) {
    const proto = list.get("x-forwarded-proto") === "http" ? "http" : "https";
    return `${proto}://${host}`;
  }
  return siteConfig.url;
}

export type AuthFlow = "google" | "signup" | "recovery";

/** Where Supabase sends people after Google or an email link. /auth/callback finishes the sign in. */
export function authCallbackUrl(origin: string, flow: AuthFlow, next?: string | null): string {
  const url = new URL("/auth/callback", origin);
  url.searchParams.set("flow", flow);
  if (next) url.searchParams.set("next", next);
  return url.toString();
}
