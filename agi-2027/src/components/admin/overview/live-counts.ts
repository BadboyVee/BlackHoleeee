import type { ApplicationRow, SignupRow } from "@/lib/creators/queries";

/*
 * The live overview's numbers, from real applications and sign ups only.
 * Plain functions with no React, so they're easy to test.
 */

export type OverviewCounts = { waiting: number; approved: number; notApplied: number };

export function overviewCounts(rows: readonly ApplicationRow[], signups: readonly SignupRow[]): OverviewCounts {
  return {
    waiting: rows.filter((row) => row.status === "submitted").length,
    approved: rows.filter((row) => row.status === "approved").length,
    notApplied: signups.length,
  };
}

/** The applications waiting longest, oldest first, at most `limit`. */
export function oldestWaiting(rows: readonly ApplicationRow[], limit = 5): ApplicationRow[] {
  return rows
    .filter((row) => row.status === "submitted")
    .sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt))
    .slice(0, limit);
}
