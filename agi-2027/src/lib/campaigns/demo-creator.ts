import { isVisibleToCreator, type CreatorClaim } from "@/lib/campaigns/claims";
import {
  canSee,
  clientById,
  demoCampaigns,
  demoMe,
  demoMyClaims,
  payoutFor,
  type DemoCampaign,
  type DemoCreator,
} from "@/lib/campaigns/demo";
import type { ClaimMode, Deliverable, Platform } from "@/lib/campaigns/options";
import type { CampaignStatus } from "@/lib/statuses";

/**
 * Demo data for the creator screens, on top of the shared demo in demo.ts:
 * one extra apply-mode drop, a little history (past campaigns, two payments,
 * an approval waiting to be paid and an expired claim) and richer detail for
 * the demo creator's claims.
 *
 * It also builds the creator's view of each campaign. That view leaves out
 * the budget, admin notes, audience rules and other creators' payouts, so the
 * browser only ever receives what a creator may see. Import values from this
 * file in Server Components only; Client Components import its types.
 */

/** What a creator sees of a campaign. Their own payout only. */
export type CreatorCampaign = {
  id: string;
  title: string;
  summary: string;
  status: CampaignStatus;
  brand: { name: string; initials: string; color: string; xHandle: string; website: string };
  /** This creator's payout: their own amount, else their tier's, else the base. */
  payout: { amount: string; currency: string };
  slots: number;
  slotsTaken: number;
  claimMode: ClaimMode;
  draftRequired: boolean;
  paidLabelRequired: boolean;
  platform: Platform;
  deliverable: Deliverable;
  brief: DemoCampaign["brief"];
  angles: string[];
  links: DemoCampaign["links"];
  requiredTags: DemoCampaign["requiredTags"];
  assets: DemoCampaign["assets"];
  timing: Omit<DemoCampaign["timing"], "dropAt">;
  /** When it reached creators (the creation time for older data). */
  droppedAt: string;
};

export type CreatorMe = {
  id: string;
  name: string;
  firstName: string;
  handle: string;
  initials: string;
  tier: string;
};

export type CreatorDemo = {
  me: CreatorMe;
  campaigns: CreatorCampaign[];
  /** The claims the demo starts from. The browser keeps its own copy once you act. */
  claims: CreatorClaim[];
};

const dos = ["Use the paid partnership label", "Post inside your window", "Write it in your own voice"];
const donts = ["Don't promise returns or results", "Don't tag competitors", "Don't use the brand's logo as your avatar"];

const pastBase = {
  tierPayouts: [],
  creatorPayouts: [],
  requests: 0,
  audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
  paidLabelRequired: true,
  assets: { brandKitUrl: "", files: [] },
} satisfies Partial<DemoCampaign>;

/**
 * One open drop that only the creator screens know about: the shared demo has
 * no apply-mode campaign the demo creator hasn't already joined, and without
 * one nobody could try "Request to join".
 */
export const demoCreatorDrops: DemoCampaign[] = [
  {
    ...pastBase,
    id: "cmp-quill-agent",
    clientId: "c-quill",
    status: "live",
    title: "Docs agent private beta",
    summary: "Six creators get early access to Quill & Wire's docs agent and post their honest first week.",
    brief: {
      about: "Quill & Wire is a writing tool for technical teams. Its new docs agent keeps pages up to date as the code changes.",
      whatToSay: "Point the agent at a real repo for a week, then post what it kept up to date and what it missed.",
      keyMessage: "Docs that update themselves when the code does.",
      dos,
      donts,
    },
    angles: ["What it caught that you would have missed", "A week of docs you didn't write", "Where it still needs a human"],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://quillwire.example/agent?ref=agi2027" },
    requiredTags: { mentions: ["@quillwire"], hashtags: ["#DocsAgent"], keywords: [] },
    assets: {
      brandKitUrl: "https://quillwire.example/press",
      files: [{ name: "docs-agent-walkthrough.mp4", kind: "video", sizeBytes: 24_800_000 }],
    },
    payout: { amount: "75", currency: "USDT" },
    slots: 6,
    slotsTaken: 2,
    requests: 4,
    claimMode: "apply",
    draftRequired: false,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-09T15:00:00Z",
      postWindowEnd: "2026-11-09T19:00:00Z",
      claimDeadline: "2026-11-08T12:00:00Z",
      proofDeadline: "2026-11-10T12:00:00Z",
    },
    internal: { notes: "", budgetAmount: "", budgetCurrency: "USDT" },
    createdAt: "2026-11-01T12:00:00Z",
    droppedAt: "2026-11-02T14:00:00Z",
  },
];

/** Campaigns that finished before the current drops. Only the creator screens use them. */
export const demoPastCampaigns: DemoCampaign[] = [
  {
    ...pastBase,
    id: "cmp-hist-quill-docs",
    clientId: "c-quill",
    status: "closed",
    title: "Docs week: one habit",
    summary: "Share one documentation habit that saved your team, and how Quill & Wire keeps it alive.",
    brief: {
      about: "Quill & Wire is a writing tool for technical teams. Docs week celebrates the habits that keep docs alive.",
      whatToSay: "Tell one short story about a doc that saved your team, and the habit behind it.",
      keyMessage: "Docs your whole team actually keeps up to date.",
      dos,
      donts,
    },
    angles: ["The doc that saved a launch", "A five-minute weekly habit"],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://quillwire.example/docs-week?ref=agi2027" },
    requiredTags: { mentions: ["@quillwire"], hashtags: ["#DocsWeek"], keywords: [] },
    payout: { amount: "95000", currency: "NGN" },
    slots: 10,
    slotsTaken: 8,
    claimMode: "instant",
    draftRequired: false,
    timing: {
      dropAt: "",
      postWindowStart: "2026-10-06T14:00:00Z",
      postWindowEnd: "2026-10-06T18:00:00Z",
      claimDeadline: "2026-10-06T10:00:00Z",
      proofDeadline: "2026-10-07T12:00:00Z",
    },
    internal: { notes: "", budgetAmount: "", budgetCurrency: "NGN" },
    createdAt: "2026-10-01T09:00:00Z",
    droppedAt: "2026-10-02T09:00:00Z",
  },
  {
    ...pastBase,
    id: "cmp-hist-lumen-call",
    clientId: "c-lumen",
    status: "completed",
    title: "Community call recap",
    summary: "A short thread on the three best answers from Lumen's open community call.",
    brief: {
      about: "Lumen Labs trains small open models that run on a laptop. They host an open community call every month.",
      whatToSay: "Pick the three answers that stuck with you and turn them into a short thread.",
      keyMessage: "Open models, built in the open.",
      dos,
      donts,
    },
    angles: ["The answer that surprised the room", "What builders asked most"],
    deliverable: "thread",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://lumenlabs.example/community?ref=agi2027" },
    requiredTags: { mentions: ["@lumenlabs"], hashtags: [], keywords: ["community call"] },
    payout: { amount: "200", currency: "USD" },
    slots: 6,
    slotsTaken: 6,
    claimMode: "apply",
    draftRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-09-29T16:00:00Z",
      postWindowEnd: "2026-09-29T20:00:00Z",
      claimDeadline: "2026-09-28T18:00:00Z",
      proofDeadline: "2026-09-30T12:00:00Z",
    },
    internal: { notes: "", budgetAmount: "", budgetCurrency: "USD" },
    createdAt: "2026-09-22T09:00:00Z",
    droppedAt: "2026-09-24T12:00:00Z",
  },
  {
    ...pastBase,
    id: "cmp-hist-orbitar-alpha",
    clientId: "c-orbitar",
    status: "completed",
    title: "Alpha waitlist reply",
    summary: "Reply to Orbitar's alpha post with the first thing you'd prototype.",
    brief: {
      about: "Orbitar turns rough sketches into clickable prototypes. The alpha opened to a small waitlist.",
      whatToSay: "Reply with the first product idea you'd sketch and prototype with Orbitar.",
      keyMessage: "From napkin sketch to working prototype in one step.",
      dos,
      donts,
    },
    angles: ["The idea you've sat on for years"],
    deliverable: "reply",
    platform: "x",
    links: { targetPostUrl: "https://x.com/orbitar/status/1966000000000000077", trackingUrl: "" },
    requiredTags: { mentions: ["@orbitar"], hashtags: [], keywords: [] },
    payout: { amount: "40", currency: "USDT" },
    slots: 25,
    slotsTaken: 21,
    claimMode: "instant",
    draftRequired: false,
    timing: {
      dropAt: "",
      postWindowStart: "2026-09-21T15:00:00Z",
      postWindowEnd: "2026-09-21T21:00:00Z",
      claimDeadline: "2026-09-21T12:00:00Z",
      proofDeadline: "2026-09-22T12:00:00Z",
    },
    internal: { notes: "", budgetAmount: "", budgetCurrency: "USDT" },
    createdAt: "2026-09-17T09:00:00Z",
    droppedAt: "2026-09-18T10:00:00Z",
  },
  {
    ...pastBase,
    id: "cmp-hist-vectorline-playground",
    clientId: "c-vectorline",
    status: "completed",
    title: "Search playground launch",
    summary: "Show one search Vectorline gets right that keyword search gets wrong.",
    brief: {
      about: "Vectorline makes search infrastructure for AI apps. The playground lets anyone try it in the browser.",
      whatToSay: "Run one real query in the playground and show the result next to a plain keyword search.",
      keyMessage: "Search that understands what you mean.",
      dos,
      donts,
    },
    angles: ["One query, two results", "The search you gave up on"],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://vectorline.example/playground?ref=agi2027" },
    requiredTags: { mentions: ["@vectorline"], hashtags: ["#VectorlinePlayground"], keywords: [] },
    payout: { amount: "120", currency: "USDC" },
    slots: 15,
    slotsTaken: 15,
    claimMode: "instant",
    draftRequired: false,
    timing: {
      dropAt: "",
      postWindowStart: "2026-09-15T15:00:00Z",
      postWindowEnd: "2026-09-15T19:00:00Z",
      claimDeadline: "2026-09-15T12:00:00Z",
      proofDeadline: "2026-09-16T12:00:00Z",
    },
    internal: { notes: "", budgetAmount: "", budgetCurrency: "USDC" },
    createdAt: "2026-09-10T10:00:00Z",
    droppedAt: "2026-09-12T09:00:00Z",
  },
];

/** The demo creator's finished claims. */
const pastClaims: Omit<CreatorClaim, "payout">[] = [
  {
    campaignId: "cmp-hist-quill-docs",
    status: "approved",
    angle: "A five-minute weekly habit",
    proof: {
      url: "https://x.com/amarabuilds/status/1975200000000000417",
      handle: "amarabuilds",
      postId: "1975200000000000417",
      submittedAt: "2026-10-06T15:12:00Z",
    },
    events: [
      { status: "claimed", by: "you", at: "2026-10-02T09:41:00Z" },
      { status: "proof_submitted", by: "you", at: "2026-10-06T15:12:00Z" },
      { status: "approved", by: "agency", at: "2026-10-07T10:03:00Z", note: "Lovely story. The payment goes out this week." },
    ],
  },
  {
    campaignId: "cmp-hist-lumen-call",
    status: "paid",
    angle: "The answer that surprised the room",
    note: "I was on the call and took notes on every answer. Happy to turn them into a thread.",
    proof: {
      url: "https://x.com/amarabuilds/status/1972900000000000208",
      handle: "amarabuilds",
      postId: "1972900000000000208",
      submittedAt: "2026-09-29T17:05:00Z",
    },
    paidReference: "BNK-0930-4471",
    paidAt: "2026-10-02T14:30:00Z",
    events: [
      { status: "requested", by: "you", at: "2026-09-24T13:10:00Z" },
      { status: "claimed", by: "agency", at: "2026-09-25T09:00:00Z", note: "Request accepted." },
      { status: "draft_submitted", by: "you", at: "2026-09-28T19:20:00Z" },
      { status: "draft_approved", by: "agency", at: "2026-09-29T08:45:00Z" },
      { status: "proof_submitted", by: "you", at: "2026-09-29T17:05:00Z" },
      { status: "approved", by: "agency", at: "2026-09-30T10:15:00Z" },
      { status: "paid", by: "agency", at: "2026-10-02T14:30:00Z", note: "Bank transfer, reference BNK-0930-4471." },
    ],
  },
  {
    campaignId: "cmp-hist-orbitar-alpha",
    status: "expired",
    events: [
      { status: "claimed", by: "you", at: "2026-09-18T10:22:00Z" },
      {
        status: "expired",
        by: "agency",
        at: "2026-09-22T12:00:00Z",
        note: "No proof came in before the deadline, so the slot went back to the pool.",
      },
    ],
  },
  {
    campaignId: "cmp-hist-vectorline-playground",
    status: "paid",
    angle: "One query, two results",
    proof: {
      url: "https://x.com/amarabuilds/status/1967600000000000311",
      handle: "amarabuilds",
      postId: "1967600000000000311",
      submittedAt: "2026-09-15T16:02:00Z",
    },
    paidReference: "0x7c1e9b04d2f35a8e61c0b7d94e2a1f3c58d6a94f",
    paidAt: "2026-09-22T11:20:00Z",
    events: [
      { status: "claimed", by: "you", at: "2026-09-12T09:18:00Z" },
      { status: "proof_submitted", by: "you", at: "2026-09-15T16:02:00Z" },
      { status: "approved", by: "agency", at: "2026-09-16T09:30:00Z" },
      { status: "paid", by: "agency", at: "2026-09-22T11:20:00Z", note: "USDC on Base." },
    ],
  },
];

/**
 * Extra detail for the shared demo claims (demoMyClaims), keyed by campaign.
 * Their times are left out on purpose: the shared demo campaigns are dated
 * ahead of today, so a fixed time would read as the future.
 */
const currentClaimDetail: Record<string, Partial<CreatorClaim>> = {
  "cmp-nebula-2": {
    events: [{ status: "claimed", by: "you" }],
  },
  "cmp-lumen-weights": {
    note: "I test local models on my laptop every week, and most of my audience are developers who care about privacy.",
    draft: {
      text: "I ran Lumen's new 8B model on my laptop and asked it to explain my own codebase. It answered in under a second, and nothing left the machine. Open weights, real privacy. @lumenlabs #LumenOpen",
      media: [{ name: "local-run.mp4", kind: "video", sizeBytes: 18_400_000 }],
    },
    feedback: "Love the privacy angle. Can you show the moment you switch the wifi off? Lead with that.",
    events: [
      { status: "requested", by: "you" },
      { status: "claimed", by: "agency", note: "Request accepted. Your angle is privacy." },
      { status: "draft_submitted", by: "you" },
      {
        status: "changes_requested",
        by: "agency",
        note: "Love the privacy angle. Can you show the moment you switch the wifi off? Lead with that.",
      },
    ],
  },
};

function toCreatorCampaign(campaign: DemoCampaign, creator: DemoCreator): CreatorCampaign {
  const client = clientById(campaign.clientId);
  return {
    id: campaign.id,
    title: campaign.title,
    summary: campaign.summary,
    status: campaign.status,
    brand: {
      name: client?.name ?? "Brand",
      initials: client?.initials ?? campaign.title.slice(0, 2).toUpperCase(),
      color: client?.color ?? "#5c554f",
      xHandle: client?.xHandle ?? "",
      website: client?.website ?? "",
    },
    payout: payoutFor(campaign, creator),
    slots: campaign.slots,
    slotsTaken: campaign.slotsTaken,
    claimMode: campaign.claimMode,
    draftRequired: campaign.draftRequired,
    paidLabelRequired: campaign.paidLabelRequired,
    platform: campaign.platform,
    deliverable: campaign.deliverable,
    brief: campaign.brief,
    angles: campaign.angles,
    links: campaign.links,
    requiredTags: campaign.requiredTags,
    assets: campaign.assets,
    timing: {
      postWindowStart: campaign.timing.postWindowStart,
      postWindowEnd: campaign.timing.postWindowEnd,
      claimDeadline: campaign.timing.claimDeadline,
      proofDeadline: campaign.timing.proofDeadline,
    },
    droppedAt: campaign.droppedAt ?? campaign.createdAt,
  };
}

const allCampaigns = () => [...demoCampaigns, ...demoCreatorDrops, ...demoPastCampaigns];

/** A campaign the creator may open, or undefined (unknown, not dropped, or not for them). */
export function creatorCampaignById(id: string, creator: DemoCreator = demoMe): DemoCampaign | undefined {
  const campaign = allCampaigns().find((item) => item.id === id);
  return campaign && isVisibleToCreator(campaign.status, canSee(campaign, creator)) ? campaign : undefined;
}

/** Every campaign page the creator can open. */
export function creatorCampaignIds(creator: DemoCreator = demoMe): string[] {
  return allCampaigns()
    .filter((campaign) => isVisibleToCreator(campaign.status, canSee(campaign, creator)))
    .map((campaign) => campaign.id);
}

/** Everything the creator screens need, already trimmed to what a creator may see. */
export function buildCreatorDemo(creator: DemoCreator = demoMe): CreatorDemo {
  const campaigns = allCampaigns()
    .filter((campaign) => isVisibleToCreator(campaign.status, canSee(campaign, creator)))
    .map((campaign) => toCreatorCampaign(campaign, creator));
  const byId = new Map(campaigns.map((campaign) => [campaign.id, campaign]));

  const current: CreatorClaim[] = demoMyClaims
    .filter((claim) => byId.has(claim.campaignId))
    .map((claim) => {
      const detail = currentClaimDetail[claim.campaignId];
      return {
        campaignId: claim.campaignId,
        status: claim.status,
        payout: byId.get(claim.campaignId)!.payout,
        angle: claim.angle,
        postTime: claim.postTime,
        ...detail,
        events: detail?.events ?? [{ status: claim.status, by: "you" }],
      };
    });
  const past: CreatorClaim[] = pastClaims
    .filter((claim) => byId.has(claim.campaignId))
    .map((claim) => ({ ...claim, payout: byId.get(claim.campaignId)!.payout }));

  const [firstName = creator.name] = creator.name.split(/\s+/);
  const initials = creator.name
    .split(/\s+/)
    .map((part) => part[0] ?? "")
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return {
    me: {
      id: creator.id,
      name: creator.name,
      firstName,
      handle: creator.handle,
      initials,
      tier: creator.tier,
    },
    campaigns,
    claims: [...current, ...past],
  };
}
