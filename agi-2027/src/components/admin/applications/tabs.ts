import type { ApplicationRow, ApplicationStatus, SignupRow } from "@/lib/creators/queries";

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
  // People with an account and no application, so the team can remind them.
  { id: "not-applied", label: "Not applied" },
] as const;

export type ApplicationTab = (typeof APPLICATION_TABS)[number]["id"];

export const DEFAULT_TAB: ApplicationTab = "waiting";

const TAB_STATUS: Record<Exclude<ApplicationTab, "all" | "not-applied">, ApplicationStatus> = {
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

export function tabCounts(rows: readonly ApplicationRow[], notApplied = 0): Record<ApplicationTab, number> {
  const counts: Record<ApplicationTab, number> = {
    waiting: 0,
    approved: 0,
    rejected: 0,
    all: rows.length,
    "not-applied": notApplied,
  };
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
    case "not-applied":
      return [];
  }
}

/**
 * A mailto link that reminds someone to send their application. Empty when
 * there's no email to write to. "Confirm email" is off for now, so the text
 * allows for someone else having typed this address. Lines end in CRLF, as
 * mailto bodies must (RFC 6068).
 */
export function reminderHref(signup: Pick<SignupRow, "email" | "displayName">, applyUrl: string): string {
  if (!signup.email) return "";
  const name = signup.displayName.trim();
  const body = [
    `Hi${name ? ` ${name}` : ""},`,
    "",
    "This email was used to make an account on AGI 2027, but the creator application hasn't been sent yet. If that was you, finish it here:",
    applyUrl,
    "",
    "If it wasn't you, you can ignore this email.",
  ].join("\r\n");
  const query = `subject=${encodeURIComponent("Finish your AGI 2027 application")}&body=${encodeURIComponent(body)}`;
  // Keep the @ readable: some mail apps don't decode %40 in the address.
  return `mailto:${encodeURIComponent(signup.email).replaceAll("%40", "@")}?${query}`;
}
