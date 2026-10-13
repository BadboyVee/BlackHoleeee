import "server-only";

import { cacheLife } from "next/cache";

import { getSupabaseEnv } from "@/lib/supabase/env";

export type EnabledProviders = { google: boolean };

/**
 * Which sign-in methods the Supabase project has switched on, from Auth's
 * public settings. The Google button only shows once Google is set up there,
 * so nobody lands on Supabase's raw "provider is not enabled" error.
 * Cached, and checked again about once a minute.
 */
export async function enabledProviders(): Promise<EnabledProviders> {
  "use cache";
  cacheLife("minutes");

  const env = getSupabaseEnv();
  if (!env) return { google: false };
  try {
    const response = await fetch(`${env.url}/auth/v1/settings`, {
      headers: { apikey: env.publishableKey },
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return { google: false };
    const settings = (await response.json()) as { external?: { google?: unknown } };
    return { google: settings.external?.google === true };
  } catch {
    return { google: false };
  }
}
