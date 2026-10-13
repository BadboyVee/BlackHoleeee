import { liveStatus, slotsLeft } from "@/lib/campaigns/claims";
import { clientById, demoCampaigns, type DemoCampaign } from "@/lib/campaigns/demo";
import { demoCreatorDrops } from "@/lib/campaigns/demo-creator";
import type { ClaimMode, Deliverable, Platform } from "@/lib/campaigns/options";

/**
 * The public /campaigns board: a teaser anyone can read without signing in.
 *
 * It only shows campaigns that are live or full right now and open to every
 * creator. Hand-picked, tier and tag campaigns are private, so they never
 * appear here. Each campaign is copied field by field into a PublicCampaign
 * (never spread), so payouts, budgets, notes, rosters and audience rules
 * can't leak onto the page, not even by accident when the source gains a field.
 *
 * Milestone 5 swaps the demo data for a database function that returns these
 * same safe fields (PLAN.md, key decision 3), and the page keeps working as is.
 */

/** What anyone may see of a campaign. No payout, budget, notes, roster or audience. */
export type PublicCampaign = {
  id: string;
  brand: { name: string; initials: string; color: string };
  title: string;
  summary: string;
  platform: Platform;
  deliverable: Deliverable;
  /** UTC ISO times. */
  postWindow: { start: string; end: string };
  slots: { total: number; taken: number };
  status: "live" | "full";
  claimMode: ClaimMode;
  /** When it reached creators (UTC ISO). */
  droppedAt: string;
};

/**
 * The moment the demo data describes: the afternoon of Tue 3 Nov 2026,
 * Nebula's launch day (the owner screens use the same instant as DEMO_NOW).
 * The demo is a fixed snapshot dated ahead of today, so against the real
 * clock every drop would read as "not out yet" and the board would be empty.
 */
export const DEMO_BOARD_NOW = "2026-11-03T19:00:00Z";

const NEUTRAL_BRAND = "#6b635f";

/** The shared demo plus the creator screens' extra open drop, so both boards agree. */
const demoSource: readonly DemoCampaign[] = [...demoCampaigns, ...demoCreatorDrops];

function toPublicCampaign(campaign: DemoCampaign, status: PublicCampaign["status"]): PublicCampaign {
  const client = clientById(campaign.clientId);
  return {
    id: campaign.id,
    brand: {
      name: client?.name ?? "A startup",
      initials: client?.initials ?? campaign.title.slice(0, 2).toUpperCase(),
      color: client?.color ?? NEUTRAL_BRAND,
    },
    title: campaign.title,
    summary: campaign.summary,
    platform: campaign.platform,
    deliverable: campaign.deliverable,
    postWindow: { start: campaign.timing.postWindowStart, end: campaign.timing.postWindowEnd },
    slots: { total: campaign.slots, taken: Math.min(campaign.slotsTaken, campaign.slots) },
    status,
    claimMode: campaign.claimMode,
    droppedAt: campaign.droppedAt ?? campaign.createdAt,
  };
}

/**
 * Campaigns the public board shows at `now`, newest drop first: open to all
 * creators, live or full (Live turns Full when the last slot goes), already
 * dropped, and with a post window that hasn't ended.
 */
export function publicCampaigns(now: Date, source: readonly DemoCampaign[] = demoSource): PublicCampaign[] {
  const nowMs = now.getTime();
  const board: PublicCampaign[] = [];
  for (const campaign of source) {
    if (campaign.audience.kind !== "all") continue;
    const status = liveStatus(campaign.status, slotsLeft(campaign));
    if (status !== "live" && status !== "full") continue;
    const dropped = Date.parse(campaign.droppedAt ?? campaign.createdAt);
    const windowEnd = Date.parse(campaign.timing.postWindowEnd);
    if (!(dropped <= nowMs) || !(windowEnd > nowMs)) continue;
    board.push(toPublicCampaign(campaign, status));
  }
  return board.sort((a, b) => Date.parse(b.droppedAt) - Date.parse(a.droppedAt));
}

/** Where a campaign's button sends people: sign up, then straight to that campaign. */
export function publicCampaignSignupHref(id: string): string {
  return `/signup?next=/dashboard/campaigns/${encodeURIComponent(id)}`;
}
