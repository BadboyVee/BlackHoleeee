import {
  campaignById,
  clientById,
  creatorById,
  demoCampaigns,
  demoRosters,
  payoutFor,
  type DemoCampaign,
  type DemoClient,
  type DemoCreator,
  type DemoRosterRow,
} from "@/lib/campaigns/demo";
import { totalsByCurrency } from "@/lib/money";
import type { CampaignStatus, ClaimStatus } from "@/lib/statuses";

/**
 * Numbers the owner screens show, worked out from the demo data so every
 * screen agrees with every other one. Milestones 5 to 9 swap these for
 * database queries. The demo world is set on the afternoon of Tue 3 Nov 2026,
 * Nebula's launch day.
 */

export const DEMO_NOW = "2026-11-03T19:00:00Z";
const DEMO_DAY = DEMO_NOW.slice(0, 10);
const DEMO_MONTH = DEMO_NOW.slice(0, 7);

/** Statuses where the agency has to act. */
export const WAITING_STATUSES: ReadonlySet<ClaimStatus> = new Set(["requested", "draft_submitted", "proof_submitted"]);
/** Statuses that hold a slot on the campaign. */
export const SLOT_STATUSES: ReadonlySet<ClaimStatus> = new Set([
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
  "proof_submitted",
  "approved",
  "rejected",
  "paid",
]);

export type RosterEntry = DemoRosterRow & { creator: DemoCreator; payout: { amount: string; currency: string } };

export function rosterFor(campaign: DemoCampaign): RosterEntry[] {
  return (demoRosters[campaign.id] ?? []).flatMap((row) => {
    const creator = creatorById(row.creatorId);
    return creator ? [{ ...row, creator, payout: payoutFor(campaign, creator) }] : [];
  });
}

export function waitingCount(campaignId: string) {
  return (demoRosters[campaignId] ?? []).filter((row) => WAITING_STATUSES.has(row.status)).length;
}

export type CampaignStats = {
  slotsTaken: number;
  slots: number;
  requests: number;
  waiting: number;
  postsLive: number;
  approved: number;
  paid: number;
  views: number;
};

export function campaignStats(campaign: DemoCampaign): CampaignStats {
  const rows = demoRosters[campaign.id] ?? [];
  return {
    slotsTaken: campaign.slotsTaken,
    slots: campaign.slots,
    requests: rows.filter((row) => row.status === "requested").length,
    waiting: rows.filter((row) => WAITING_STATUSES.has(row.status)).length,
    postsLive: rows.filter((row) => row.postUrl && row.status !== "rejected").length,
    approved: rows.filter((row) => row.status === "approved" || row.status === "paid").length,
    paid: rows.filter((row) => row.status === "paid").length,
    views: rows.reduce((sum, row) => sum + (row.views ?? 0), 0),
  };
}

export type ReviewItem = {
  kind: "Request" | "Draft" | "Proof";
  campaign: DemoCampaign;
  client: DemoClient | undefined;
  creator: DemoCreator;
  at: string;
  /** Milliseconds it has been waiting, measured from the demo clock. */
  waitingMs: number;
};

const reviewKind: Partial<Record<ClaimStatus, ReviewItem["kind"]>> = {
  requested: "Request",
  draft_submitted: "Draft",
  proof_submitted: "Proof",
};

/** Everything waiting on the agency, oldest first. */
export function reviewQueue(): ReviewItem[] {
  const items: ReviewItem[] = [];
  for (const campaign of demoCampaigns) {
    for (const row of demoRosters[campaign.id] ?? []) {
      const kind = reviewKind[row.status];
      const creator = creatorById(row.creatorId);
      if (!kind || !creator) continue;
      const at = row.at ?? campaign.createdAt;
      items.push({
        kind,
        campaign,
        client: clientById(campaign.clientId),
        creator,
        at,
        waitingMs: Math.max(0, new Date(DEMO_NOW).getTime() - new Date(at).getTime()),
      });
    }
  }
  return items.sort((a, b) => a.at.localeCompare(b.at));
}

export const reviewCount = () => reviewQueue().length;

export function campaignsByStatus(status: CampaignStatus) {
  return demoCampaigns.filter((campaign) => campaign.status === status);
}

/** Earnings created by approved proof and not paid yet, per currency. */
export function unpaidTotals() {
  return totalsByCurrency(
    demoCampaigns.flatMap((campaign) =>
      rosterFor(campaign)
        .filter((row) => row.status === "approved")
        .map((row) => row.payout),
    ),
  );
}

/** Paid in the demo month, per currency. */
export function paidThisMonth() {
  return totalsByCurrency(
    demoCampaigns.flatMap((campaign) =>
      rosterFor(campaign)
        .filter((row) => row.status === "paid" && row.at?.startsWith(DEMO_MONTH))
        .map((row) => row.payout),
    ),
  );
}

/** Claims with a post time on the demo day that haven't posted yet. */
export function postsDueToday() {
  return demoCampaigns.flatMap((campaign) =>
    rosterFor(campaign)
      .filter(
        (row) =>
          row.postTime?.startsWith(DEMO_DAY) &&
          (row.status === "claimed" || row.status === "draft_approved"),
      )
      .map((row) => ({ campaign, row })),
  );
}

export function campaignWithClient(id: string) {
  const campaign = campaignById(id);
  if (!campaign) return undefined;
  return { campaign, client: clientById(campaign.clientId) };
}

/** Applications and leads arrive in Milestones 4 and 9; these stand in until then. */
export const demoApplications = [
  { name: "Tomás Ruiz", handle: "@tomasbuilds", followers: 14200, niche: "AI builders", at: "2026-11-03T15:10:00Z" },
  { name: "Grace Owusu", handle: "@graceonchain", followers: 21800, niche: "Crypto", at: "2026-11-03T11:42:00Z" },
  { name: "Arjun Mehta", handle: "@arjunships", followers: 9100, niche: "Dev tools", at: "2026-11-02T20:05:00Z" },
  { name: "Elena Popescu", handle: "@elenadesigns", followers: 33500, niche: "Design", at: "2026-11-02T09:30:00Z" },
];

export const demoLeads = [
  { company: "Parallax", contact: "Mina Cho", launching: "Series A announcement", budget: "$10k to $25k", at: "2026-11-03T16:20:00Z" },
  { company: "Helix Robotics", contact: "Sam Okoro", launching: "Open beta", budget: "$5k to $10k", at: "2026-11-03T10:05:00Z" },
  { company: "Northwind AI", contact: "Ivy Chen", launching: "Model release", budget: "$25k+", at: "2026-11-02T18:40:00Z" },
];

/**
 * Posts approved and payouts sent per week, for the overview chart. Twelve
 * weeks ending with the demo week; the last week is still in progress.
 */
export const weeklyActivity = [
  { week: "2026-08-17", posts: 6, paid: { USD: "600", USDC: "0", NGN: "0" } },
  { week: "2026-08-24", posts: 9, paid: { USD: "900", USDC: "240", NGN: "0" } },
  { week: "2026-08-31", posts: 4, paid: { USD: "400", USDC: "0", NGN: "180000" } },
  { week: "2026-09-07", posts: 12, paid: { USD: "1350", USDC: "360", NGN: "0" } },
  { week: "2026-09-14", posts: 10, paid: { USD: "1100", USDC: "480", NGN: "360000" } },
  { week: "2026-09-21", posts: 15, paid: { USD: "1500", USDC: "600", NGN: "0" } },
  { week: "2026-09-28", posts: 8, paid: { USD: "800", USDC: "240", NGN: "540000" } },
  { week: "2026-10-05", posts: 14, paid: { USD: "500", USDC: "720", NGN: "0" } },
  { week: "2026-10-12", posts: 18, paid: { USD: "1800", USDC: "960", NGN: "360000" } },
  { week: "2026-10-19", posts: 11, paid: { USD: "1200", USDC: "480", NGN: "0" } },
  { week: "2026-10-26", posts: 21, paid: { USD: "2400", USDC: "1320", NGN: "135000" } },
  { week: "2026-11-02", posts: 5, paid: { USD: "500", USDC: "570", NGN: "0" } },
] as const;

export const CHART_CURRENCIES = ["USD", "USDC", "NGN"] as const;
