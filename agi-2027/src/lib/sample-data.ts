import type { CampaignCardData } from "@/components/campaign/campaign-card";

/**
 * Sample data for the preview screens, so the portal and admin can be judged
 * before real data exists. Fictional brands and people. Replaced by live data
 * from Milestone 5 on; nothing here is ever written to the database.
 */

export const sampleCampaigns: CampaignCardData[] = [
  {
    href: "/dashboard/campaigns",
    brand: { name: "Nebula AI", initials: "NA" },
    title: "Nebula 2.0 launch day",
    summary: "Quote the launch post with your honest first take on Nebula's new agent builder.",
    payout: { amount: "250", currency: "USDC" },
    slots: { total: 20, taken: 13 },
    platform: "x",
    deliverable: "Quote post",
    postWindow: { start: "2026-11-03T16:00:00Z", end: "2026-11-03T20:00:00Z" },
    status: "live",
    isNew: true,
  },
  {
    href: "/dashboard/campaigns",
    brand: { name: "Lumen Labs", initials: "LL" },
    title: "Open-weights model drop",
    summary: "A 30–60 second clip of the model running locally, with your one-line verdict.",
    payout: { amount: "400", currency: "USD" },
    slots: { total: 8, taken: 2 },
    platform: "x",
    deliverable: "Video",
    postWindow: { start: "2026-11-05T15:00:00Z", end: "2026-11-05T21:00:00Z" },
    status: "live",
    isNew: true,
  },
  {
    href: "/dashboard/campaigns",
    brand: { name: "Orbitar", initials: "OR" },
    title: "Design agent public beta",
    summary: "Show a sketch-to-prototype in one post. Your angle is assigned when you claim.",
    payout: { amount: "150", currency: "USD" },
    slots: { total: 30, taken: 9 },
    platform: "x",
    deliverable: "Original post",
    postWindow: { start: "2026-11-07T14:00:00Z", end: "2026-11-08T14:00:00Z" },
    status: "live",
  },
  {
    href: "/dashboard/campaigns",
    brand: { name: "Vectorline", initials: "VL" },
    title: "Series A announcement",
    summary: "A short thread on what Vectorline's raise means for teams building search.",
    payout: { amount: "180000", currency: "NGN" },
    slots: { total: 12, taken: 12 },
    platform: "x",
    deliverable: "Thread",
    postWindow: { start: "2026-11-04T13:00:00Z", end: "2026-11-04T17:00:00Z" },
    status: "full",
  },
];

export const sampleCreatorActions = [
  {
    kind: "Proof due",
    campaign: "Nebula 2.0 launch day",
    brand: "Nebula AI",
    detail: "Post inside your window, then paste the link.",
    due: "2026-11-03T20:00:00Z",
    status: "claimed" as const,
  },
  {
    kind: "Changes requested",
    campaign: "Design agent public beta",
    brand: "Orbitar",
    detail: "“Lead with the prototype, and add #OrbitarBeta.”",
    due: "2026-11-06T12:00:00Z",
    status: "changes_requested" as const,
  },
];

export const sampleEarnings = {
  unpaid: [
    { amount: "250", currency: "USDC" },
    { amount: "180000", currency: "NGN" },
  ],
  paidThisMonth: [{ amount: "1150", currency: "USD" }],
};

export const sampleAdminStats = [
  { label: "Live campaigns", value: "3" },
  { label: "Posts due today", value: "12" },
  { label: "Waiting for review", value: "7", highlight: true },
  { label: "New applications", value: "4" },
];

export const sampleMoney = {
  unpaid: [
    { amount: "3450", currency: "USD" },
    { amount: "480000", currency: "NGN" },
  ],
  paidThisMonth: [
    { amount: "8200", currency: "USD" },
    { amount: "1250", currency: "USDC" },
  ],
};

export const sampleReviewQueue = [
  {
    creator: { name: "Mira Okafor", handle: "mira_builds", initials: "MO", hue: 95 },
    type: "Proof",
    campaign: "Nebula 2.0 launch day",
    waiting: "2h",
    checks: [
      { label: "Handle matches", ok: true },
      { label: "Inside window", ok: true },
      { label: "Tags found", ok: true },
    ],
  },
  {
    creator: { name: "Kai Moreno", handle: "kai_codes", initials: "KM", hue: 280 },
    type: "Draft",
    campaign: "Design agent public beta",
    waiting: "5h",
    checks: [],
  },
  {
    creator: { name: "Devon Hale", handle: "devonships", initials: "DH", hue: 210 },
    type: "Proof",
    campaign: "Series A announcement",
    waiting: "1d",
    checks: [
      { label: "Handle matches", ok: true },
      { label: "Inside window", ok: true },
      { label: "Missing #Vectorline", ok: false },
    ],
  },
  {
    creator: { name: "Ada Nwosu", handle: "ada_ships", initials: "AN", hue: 30 },
    type: "Request",
    campaign: "Open-weights model drop",
    waiting: "1d",
    checks: [],
  },
];

export const sampleLiveCampaigns = [
  { title: "Nebula 2.0 launch day", brand: "Nebula AI", taken: 13, total: 20, posted: 6, status: "live" as const },
  { title: "Series A announcement", brand: "Vectorline", taken: 12, total: 12, posted: 9, status: "full" as const },
  { title: "Open-weights model drop", brand: "Lumen Labs", taken: 2, total: 8, posted: 0, status: "live" as const },
];
