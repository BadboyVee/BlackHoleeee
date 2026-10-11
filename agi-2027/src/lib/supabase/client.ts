import { createBrowserClient } from "@supabase/ssr";

import { requireSupabaseEnv } from "./env";

/** Supabase client for Client Components. Uses the signed-in user's session. */
export function createClient() {
  const { url, publishableKey } = requireSupabaseEnv();
  return createBrowserClient(url, publishableKey);
}
