import { inviteLink, inviteStatusOf, inviteUsage } from "@/lib/creators/display";
import type { InviteRow } from "@/lib/creators/queries";
import type { InviteStatus } from "@/lib/statuses";

/*
 * An invite link as the list shows it. The server works out the status and
 * the full address (the site's address is only known there), so the client
 * components get plain data and nothing they'd have to recompute.
 */

export type InviteView = {
  id: string;
  code: string;
  /** Who it's for. Only the admin sees it. Empty when none was given. */
  label: string;
  /** The full address to share. */
  link: string;
  status: InviteStatus;
  /** "3 of 10 used", "1 use" or "No uses yet". */
  usage: string;
  uses: number;
  maxUses: number | null;
  expiresAt: string | null;
  /** The expiry is behind us, whatever else happened to the link. */
  expiryPassed: boolean;
  revokedAt: string | null;
  createdAt: string;
};

/** Newest first, each with where it stands at `now`. */
export function toInviteViews(rows: readonly InviteRow[], now: Date): InviteView[] {
  return [...rows]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .map((row) => ({
      id: row.id,
      code: row.code,
      label: row.label.trim(),
      link: inviteLink(row.code),
      status: inviteStatusOf(row, now),
      usage: inviteUsage(row),
      uses: row.uses,
      maxUses: row.maxUses,
      expiresAt: row.expiresAt,
      expiryPassed: row.expiresAt !== null && new Date(row.expiresAt).getTime() <= now.getTime(),
      revokedAt: row.revokedAt,
      createdAt: row.createdAt,
    }));
}
