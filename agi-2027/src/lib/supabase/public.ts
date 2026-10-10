import "server-only";

import { createClient as createSupabaseClient } from "@supabase/supabase-js";

import { requireSupabaseEnv } from "./env";

/**
 * Anonymous Supabase client with no session, for public reads such as the
 * open campaigns board and health checks. RLS applies as the anon role.
 */
export function createPublicClient() {
  const { url, publishableKey } = requireSupabaseEnv();
  return createSupabaseClient(url, publishableKey, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  });
}
