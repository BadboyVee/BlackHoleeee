import { connection } from "next/server";

import { StatusDot } from "@/components/status-badge";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createPublicClient } from "@/lib/supabase/public";
import type { Tone } from "@/lib/statuses";

type Health = { ok: boolean; db_time: string; schema_version: string };

async function checkSupabase(): Promise<{ tone: Tone; label: string; detail: string }> {
  if (!getSupabaseEnv()) {
    return {
      tone: "amber",
      label: "Not connected yet",
      detail: "Add the Supabase URL and publishable key to the environment.",
    };
  }
  try {
    const { data, error } = await createPublicClient()
      .rpc("health")
      .abortSignal(AbortSignal.timeout(4000));
    if (error) throw new Error(error.message);
    const health = data as Health;
    return {
      tone: "green",
      label: "Connected",
      detail: `Database answered at ${new Date(health.db_time).toISOString().slice(11, 19)} UTC · schema ${health.schema_version}`,
    };
  } catch (error) {
    return {
      tone: "red",
      label: "Can't reach the database",
      detail: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/** Live check that this deployment can talk to Supabase. */
async function SupabaseStatus() {
  await connection();
  const result = await checkSupabase();
  return (
    <div data-tone={result.tone} className="flex items-start gap-3">
      <span className="mt-1.5 text-(--tone-fg)">
        <StatusDot pulse={result.tone === "green"} className="size-2 [&>span]:size-2" />
      </span>
      <div className="min-w-0">
        <p className="font-medium">{result.label}</p>
        <p className="mt-0.5 text-sm break-words text-muted-foreground">{result.detail}</p>
      </div>
    </div>
  );
}

export { SupabaseStatus };
