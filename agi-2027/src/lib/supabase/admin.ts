import "server-only";

import { createClient as createSupabaseClient } from "@supabase/supabase-js";

import { requireSupabaseEnv } from "./env";

/**
 * Service client that bypasses RLS. Server-only: never import it from a
 * Client Component, and only use it where a database function can't do the
 * job (cron work, sending email, client reports). Always check the caller's
 * permissions yourself first.
 */
export function createAdminClient() {
  const { url } = requireSupabaseEnv();
  const secretKey = process.env.SUPABASE_SECRET_KEY;
  if (!secretKey) throw new Error("SUPABASE_SECRET_KEY is not set.");
  return createSupabaseClient(url, secretKey, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  });
}
