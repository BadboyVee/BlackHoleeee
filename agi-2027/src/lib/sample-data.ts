import { isLiveSite } from "@/lib/deploy";
import { getSupabaseEnv } from "@/lib/supabase/env";

/*
 * Sample campaigns, claims, leads and charts fill the admin and the creator
 * portal on preview links, so every screen can be tried. The live site never
 * shows them: there, a screen shows real data, or says plainly that there's
 * nothing yet. Both inputs are baked in at build time, so this reads the same
 * on the server and in the browser.
 */

type SampleInputs = { live: boolean; supabase: boolean };

/** Samples only off the live site, and only while no database is connected. */
export function sampleDataAllowed({ live, supabase }: SampleInputs): boolean {
  return !live && !supabase;
}

export function showSampleData(): boolean {
  return sampleDataAllowed({ live: isLiveSite(), supabase: getSupabaseEnv() !== null });
}
