import type { ApplicationRow, ApplicationStatus } from "@/lib/creators/queries";

/*
 * The filter tabs on /admin/applications and the order each one lists in.
 * Plain functions with no React, so the server page can read ?status= with
 * them and the client list can sort with them.
 */

export const APPLICATION_TABS = [
  { id: "waiting", label: "Waiting" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "all", label: "All" },
] as const;

export type ApplicationTab = (typeof APPLICATION_TABS)[number]["id"];

export const DEFAULT_TAB: ApplicationTab = "waiting";

const TAB_STATUS: Record<Exclude<ApplicationTab, "all">, ApplicationStatus> = {
  waiting: "submitted",
  approved: "approved",
  rejected: "rejected",
};

/** The tab named in the address (?status=approved), or Waiting. */
export function applicationTabFrom(value: string | null | undefined): ApplicationTab {
  return APPLICATION_TABS.find((tab) => tab.id === value)?.id ?? DEFAULT_TAB;
}

/** The address for a tab: Waiting is the plain page, the rest add ?status=. */
export function applicationTabHref(pathname: string, tab: ApplicationTab): string {
  return tab === DEFAULT_TAB ? pathname : `${pathname}?status=${tab}`;
}

export function tabCounts(rows: readonly ApplicationRow[]): Record<ApplicationTab, number> {
  const counts: Record<ApplicationTab, number> = { waiting: 0, approved: 0, rejected: 0, all: rows.length };
  for (const row of rows) {
    if (row.status === "submitted") counts.waiting += 1;
    else counts[row.status] += 1;
  }
  return counts;
}

function time(iso: string | null): number {
  const value = iso ? Date.parse(iso) : Number.NaN;
  return Number.isNaN(value) ? 0 : value;
}

/**
 * The rows a tab shows, in its order. Waiting is oldest first, so nobody
 * waits longest. Approved and Rejected show the latest decisions first; All
 * is newest first. `kept` holds applications decided from the Waiting tab
 * just now: they stay in place, showing the answer, until the tab changes.
 */
export function rowsForTab(
  rows: readonly ApplicationRow[],
  tab: ApplicationTab,
  kept: ReadonlySet<string> = new Set(),
): ApplicationRow[] {
  switch (tab) {
    case "waiting":
      return rows
        .filter((row) => row.status === "submitted" || kept.has(row.id))
        .sort((a, b) => time(a.createdAt) - time(b.createdAt));
    case "approved":
    case "rejected":
      return rows
        .filter((row) => row.status === TAB_STATUS[tab])
        .sort((a, b) => time(b.reviewedAt ?? b.createdAt) - time(a.reviewedAt ?? a.createdAt));
    case "all":
      return [...rows].sort((a, b) => time(b.createdAt) - time(a.createdAt));
  }
}
