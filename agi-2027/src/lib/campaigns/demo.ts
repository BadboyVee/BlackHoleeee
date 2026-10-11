import type { CampaignFormValues } from "@/lib/campaigns/schema";
import type { ClaimStatus, CampaignStatus } from "@/lib/statuses";

/**
 * Demo data for the owner and creator screens, so both can be tried before
 * the database exists (Milestones 5 and 6 replace it with live data). Every
 * brand and person here is made up. Nothing is ever written anywhere.
 */

export type DemoClient = {
  id: string;
  name: string;
  initials: string;
  website: string;
  xHandle: string;
  /** Brand color for the logo tile. */
  color: string;
};

export type DemoCreator = {
  id: string;
  name: string;
  handle: string;
  tier: "Tier 1" | "Tier 2" | "Tier 3";
  tags: string[];
  followers: number;
  avgViews: number;
  country: string;
};

export type DemoCampaign = Omit<CampaignFormValues, "clientId" | "newClient" | "publish"> & {
  id: string;
  clientId: string;
  status: CampaignStatus;
  slotsTaken: number;
  /** Claims waiting in apply mode (they don't hold a slot). */
  requests: number;
  createdAt: string;
  droppedAt?: string;
};

export type DemoRosterRow = {
  creatorId: string;
  status: ClaimStatus;
  angle?: string;
  postTime?: string;
  postUrl?: string;
  views?: number;
  paid: boolean;
  /** When the claim reached its current status (UTC). */
  at?: string;
};

export const demoClients: DemoClient[] = [
  { id: "c-nebula", name: "Nebula AI", initials: "NA", website: "https://nebula.example", xHandle: "@nebula_ai", color: "#5b2ee8" },
  { id: "c-lumen", name: "Lumen Labs", initials: "LL", website: "https://lumenlabs.example", xHandle: "@lumenlabs", color: "#e0252b" },
  { id: "c-orbitar", name: "Orbitar", initials: "OR", website: "https://orbitar.example", xHandle: "@orbitar", color: "#127a36" },
  { id: "c-vectorline", name: "Vectorline", initials: "VL", website: "https://vectorline.example", xHandle: "@vectorline", color: "#1e6bff" },
  { id: "c-quill", name: "Quill & Wire", initials: "QW", website: "https://quillwire.example", xHandle: "@quillwire", color: "#cf4a00" },
];

export const demoCreators: DemoCreator[] = [
  { id: "u-amara", name: "Amara Okafor", handle: "@amarabuilds", tier: "Tier 1", tags: ["AI builders", "Founders"], followers: 48200, avgViews: 31400, country: "Nigeria" },
  { id: "u-theo", name: "Theo Lindqvist", handle: "@theoships", tier: "Tier 1", tags: ["Dev tools", "AI builders"], followers: 91300, avgViews: 52800, country: "Sweden" },
  { id: "u-priya", name: "Priya Raman", handle: "@priyaprompts", tier: "Tier 2", tags: ["AI builders", "Design"], followers: 22900, avgViews: 14100, country: "India" },
  { id: "u-kwame", name: "Kwame Mensah", handle: "@kwamecodes", tier: "Tier 2", tags: ["Crypto", "Dev tools"], followers: 17600, avgViews: 9800, country: "Ghana" },
  { id: "u-lucia", name: "Lucía Ferrer", handle: "@luciaferrer", tier: "Tier 1", tags: ["Startups", "Founders"], followers: 63400, avgViews: 40200, country: "Spain" },
  { id: "u-dami", name: "Dami Adeyemi", handle: "@damiondata", tier: "Tier 3", tags: ["AI builders"], followers: 8400, avgViews: 6100, country: "Nigeria" },
  { id: "u-hana", name: "Hana Sato", handle: "@hanaonai", tier: "Tier 2", tags: ["Design", "Startups"], followers: 29800, avgViews: 17300, country: "Japan" },
  { id: "u-marcus", name: "Marcus Webb", handle: "@marcuswebb", tier: "Tier 3", tags: ["Crypto"], followers: 11200, avgViews: 7400, country: "United Kingdom" },
  { id: "u-sofia", name: "Sofia Marchetti", handle: "@sofiaships", tier: "Tier 2", tags: ["Startups", "Design"], followers: 26400, avgViews: 15200, country: "Italy" },
  { id: "u-jonah", name: "Jonah Reyes", handle: "@jonahreyes", tier: "Tier 1", tags: ["AI builders", "Dev tools"], followers: 72100, avgViews: 44600, country: "United States" },
  { id: "u-ife", name: "Ife Balogun", handle: "@ifebuilds", tier: "Tier 2", tags: ["AI builders", "Startups"], followers: 19800, avgViews: 12300, country: "Nigeria" },
  { id: "u-mei", name: "Mei Lin", handle: "@meilinai", tier: "Tier 1", tags: ["AI builders", "Design"], followers: 55900, avgViews: 33800, country: "Singapore" },
  { id: "u-oscar", name: "Oscar Nyberg", handle: "@oscarnyberg", tier: "Tier 3", tags: ["Dev tools"], followers: 9600, avgViews: 5900, country: "Norway" },
  { id: "u-zara", name: "Zara Haddad", handle: "@zarahaddad", tier: "Tier 2", tags: ["Founders", "Startups"], followers: 31200, avgViews: 19700, country: "United Arab Emirates" },
  { id: "u-leo", name: "Leo Martins", handle: "@leomartins", tier: "Tier 3", tags: ["Crypto", "AI builders"], followers: 7800, avgViews: 4700, country: "Brazil" },
  { id: "u-nadia", name: "Nadia Petrova", handle: "@nadiaprompt", tier: "Tier 2", tags: ["AI builders"], followers: 24500, avgViews: 13900, country: "Bulgaria" },
  { id: "u-chidi", name: "Chidi Eze", handle: "@chidieze", tier: "Tier 1", tags: ["Crypto", "Founders"], followers: 58700, avgViews: 36100, country: "Nigeria" },
  { id: "u-ana", name: "Ana Souza", handle: "@anasouza", tier: "Tier 3", tags: ["Design"], followers: 6900, avgViews: 4200, country: "Portugal" },
];

/** The creator the creator screens are shown as. */
export const demoMe = demoCreators[0];

const brief = (about: string, whatToSay: string, keyMessage: string) => ({
  about,
  whatToSay,
  keyMessage,
  dos: [
    "Use the paid partnership label",
    "Post inside your window",
    "Write it in your own voice",
  ],
  donts: ["Don't promise returns or results", "Don't tag competitors", "Don't use the brand's logo as your avatar"],
});

export const demoCampaigns: DemoCampaign[] = [
  {
    id: "cmp-nebula-2",
    clientId: "c-nebula",
    status: "live",
    title: "Nebula 2.0 launch day",
    summary: "Quote the launch post with your honest first take on Nebula's new agent builder.",
    brief: brief(
      "Nebula builds AI agents that run inside a company's own tools. Version 2.0 adds a visual builder anyone on a team can use.",
      "Try the builder for 10 minutes, then quote the launch post with what surprised you. Real reactions beat feature lists.",
      "Anyone on your team can build a working agent in an afternoon.",
    ),
    angles: [
      "The 10-minute build: show what you made",
      "Why this matters for non-engineers",
      "Compare it to how you built agents last year",
      "The one feature you didn't expect",
    ],
    deliverable: "quote",
    platform: "x",
    links: { targetPostUrl: "https://x.com/nebula_ai/status/1975000000000000001", trackingUrl: "https://nebula.example/?ref=agi2027" },
    requiredTags: { mentions: ["@nebula_ai"], hashtags: ["#Nebula2"], keywords: ["agent builder"] },
    assets: {
      brandKitUrl: "https://nebula.example/brand",
      files: [
        { name: "nebula-2-hero.png", kind: "image", sizeBytes: 1_840_000 },
        { name: "builder-walkthrough.mp4", kind: "video", sizeBytes: 38_200_000 },
      ],
    },
    payout: { amount: "250", currency: "USDC" },
    tierPayouts: [{ tier: "Tier 1", amount: "320" }],
    creatorPayouts: [],
    slots: 20,
    slotsTaken: 13,
    requests: 0,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-03T16:00:00Z",
      postWindowEnd: "2026-11-03T20:00:00Z",
      claimDeadline: "2026-11-03T14:00:00Z",
      proofDeadline: "2026-11-04T12:00:00Z",
    },
    internal: { notes: "Client wants 20 posts inside the first four hours.", budgetAmount: "6000", budgetCurrency: "USDC" },
    createdAt: "2026-10-28T10:12:00Z",
    droppedAt: "2026-10-30T15:00:00Z",
  },
  {
    id: "cmp-lumen-weights",
    clientId: "c-lumen",
    status: "live",
    title: "Open-weights model drop",
    summary: "A 30 to 60 second clip of the model running locally, with your one-line verdict.",
    brief: brief(
      "Lumen Labs trains small open models that run on a laptop. Their new 8B model ships with open weights.",
      "Record the model answering a real question on your machine. End with a one-line verdict.",
      "A frontier-class model that runs on your own laptop.",
    ),
    angles: ["Speed test on your laptop", "Privacy: nothing leaves the machine", "Coding help offline"],
    deliverable: "video",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://lumenlabs.example/download?ref=agi2027" },
    requiredTags: { mentions: ["@lumenlabs"], hashtags: ["#LumenOpen"], keywords: [] },
    assets: { brandKitUrl: "", files: [{ name: "lumen-logo-pack.zip", kind: "document", sizeBytes: 4_200_000 }] },
    payout: { amount: "400", currency: "USD" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 8,
    slotsTaken: 2,
    requests: 3,
    audience: { kind: "tags", tiers: [], tags: ["AI builders", "Dev tools"], creatorIds: [] },
    claimMode: "apply",
    draftRequired: true,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-05T15:00:00Z",
      postWindowEnd: "2026-11-05T21:00:00Z",
      claimDeadline: "2026-11-04T18:00:00Z",
      proofDeadline: "2026-11-06T12:00:00Z",
    },
    internal: { notes: "Drafts must show the model running, not slides.", budgetAmount: "3500", budgetCurrency: "USD" },
    createdAt: "2026-10-29T09:00:00Z",
    droppedAt: "2026-10-31T12:00:00Z",
  },
  {
    id: "cmp-orbitar-beta",
    clientId: "c-orbitar",
    status: "live",
    title: "Design agent public beta",
    summary: "Show a sketch-to-prototype in one post. Your angle is assigned when you claim.",
    brief: brief(
      "Orbitar turns rough sketches into clickable prototypes. The public beta opens this week.",
      "Sketch something on paper, run it through Orbitar and post the before and after.",
      "From napkin sketch to working prototype in one step.",
    ),
    angles: ["Before and after", "A real product idea you've had for years", "Speedrun: sketch to prototype"],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://orbitar.example/beta?ref=agi2027" },
    requiredTags: { mentions: ["@orbitar"], hashtags: ["#OrbitarBeta"], keywords: [] },
    assets: { brandKitUrl: "https://orbitar.example/press", files: [] },
    payout: { amount: "150", currency: "USD" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 30,
    slotsTaken: 9,
    requests: 0,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: true,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-07T14:00:00Z",
      postWindowEnd: "2026-11-08T14:00:00Z",
      claimDeadline: "2026-11-07T10:00:00Z",
      proofDeadline: "2026-11-08T20:00:00Z",
    },
    internal: { notes: "", budgetAmount: "5000", budgetCurrency: "USD" },
    createdAt: "2026-10-30T08:30:00Z",
    droppedAt: "2026-11-01T09:00:00Z",
  },
  {
    id: "cmp-vectorline-a",
    clientId: "c-vectorline",
    status: "full",
    title: "Series A announcement",
    summary: "A short thread on what Vectorline's raise means for teams building search.",
    brief: brief(
      "Vectorline makes search infrastructure for AI apps. They just raised a Series A.",
      "Write a short thread: the problem Vectorline solves, why the raise matters, and who should try it.",
      "Search that understands meaning, now with the funding to scale.",
    ),
    angles: ["The problem in one example", "What the raise unlocks", "Who should try it this week"],
    deliverable: "thread",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "" },
    requiredTags: { mentions: ["@vectorline"], hashtags: [], keywords: ["Series A"] },
    assets: { brandKitUrl: "", files: [] },
    payout: { amount: "180000", currency: "NGN" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 12,
    slotsTaken: 12,
    requests: 0,
    audience: { kind: "tiers", tiers: ["Tier 1", "Tier 2"], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-04T13:00:00Z",
      postWindowEnd: "2026-11-04T17:00:00Z",
      claimDeadline: "2026-11-04T11:00:00Z",
      proofDeadline: "2026-11-05T12:00:00Z",
    },
    internal: { notes: "Paid in NGN at the client's request.", budgetAmount: "2200000", budgetCurrency: "NGN" },
    createdAt: "2026-10-27T13:00:00Z",
    droppedAt: "2026-10-29T10:00:00Z",
  },
  {
    id: "cmp-quill-founder",
    clientId: "c-quill",
    status: "scheduled",
    title: "Founder story: building in public",
    summary: "Reply to the founder's post with what you'd build on Quill & Wire.",
    brief: brief(
      "Quill & Wire is a writing tool for technical teams. Their founder is sharing the story of year one.",
      "Reply to the founder's post with one specific thing you'd build or write with the product.",
      "Docs your whole team actually keeps up to date.",
    ),
    angles: ["What you'd document first", "A team habit it fixes"],
    deliverable: "reply",
    platform: "x",
    links: { targetPostUrl: "https://x.com/quillwire/status/1975000000000000002", trackingUrl: "" },
    requiredTags: { mentions: ["@quillwire"], hashtags: [], keywords: [] },
    assets: { brandKitUrl: "", files: [] },
    payout: { amount: "60", currency: "USDT" },
    tierPayouts: [],
    creatorPayouts: [
      { creatorId: "u-lucia", amount: "90" },
      { creatorId: "u-theo", amount: "90" },
    ],
    slots: 4,
    slotsTaken: 0,
    requests: 0,
    audience: { kind: "creators", tiers: [], tags: [], creatorIds: ["u-amara", "u-theo", "u-lucia", "u-hana"] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "2026-11-09T09:00:00Z",
      postWindowStart: "2026-11-10T15:00:00Z",
      postWindowEnd: "2026-11-10T18:00:00Z",
      claimDeadline: "2026-11-10T12:00:00Z",
      proofDeadline: "2026-11-11T12:00:00Z",
    },
    internal: { notes: "Founder will like and reply to the best ones.", budgetAmount: "300", budgetCurrency: "USDT" },
    createdAt: "2026-11-01T16:20:00Z",
  },
  {
    id: "cmp-nebula-draft",
    clientId: "c-nebula",
    status: "draft",
    title: "Nebula agents: customer stories",
    summary: "Short posts on how teams use Nebula agents day to day.",
    brief: brief(
      "Nebula builds AI agents that run inside a company's own tools.",
      "Pick one of the customer stories in the assets and retell it in your words.",
      "Agents that do real work inside the tools you already use.",
    ),
    angles: [],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "" },
    requiredTags: { mentions: ["@nebula_ai"], hashtags: [], keywords: [] },
    assets: { brandKitUrl: "", files: [] },
    payout: { amount: "120", currency: "USDC" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 15,
    slotsTaken: 0,
    requests: 0,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-14T15:00:00Z",
      postWindowEnd: "2026-11-15T15:00:00Z",
      claimDeadline: "2026-11-14T12:00:00Z",
      proofDeadline: "2026-11-16T12:00:00Z",
    },
    internal: { notes: "Waiting on the client to approve the stories.", budgetAmount: "", budgetCurrency: "USDC" },
    createdAt: "2026-11-02T11:00:00Z",
  },
  {
    id: "cmp-lumen-code",
    clientId: "c-lumen",
    status: "paused",
    title: "Lumen Code early access",
    summary: "A short post on your first hour with Lumen Code, the offline coding assistant.",
    brief: brief(
      "Lumen Labs trains small open models that run on a laptop. Lumen Code is their offline coding assistant.",
      "Use Lumen Code on a real task for an hour, then post what it got right and what it didn't.",
      "A coding assistant that never sends your code anywhere.",
    ),
    angles: ["Your first hour, honestly", "Working on a plane or a train", "Privacy for client work"],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://lumenlabs.example/code?ref=agi2027" },
    requiredTags: { mentions: ["@lumenlabs"], hashtags: ["#LumenCode"], keywords: [] },
    assets: { brandKitUrl: "", files: [{ name: "lumen-code-screens.zip", kind: "document", sizeBytes: 9_600_000 }] },
    payout: { amount: "200", currency: "USD" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 10,
    slotsTaken: 4,
    requests: 0,
    audience: { kind: "tags", tiers: [], tags: ["Dev tools"], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-11-12T15:00:00Z",
      postWindowEnd: "2026-11-12T21:00:00Z",
      claimDeadline: "2026-11-12T12:00:00Z",
      proofDeadline: "2026-11-13T12:00:00Z",
    },
    internal: { notes: "Paused at the client's request while they fix an install bug.", budgetAmount: "2000", budgetCurrency: "USD" },
    createdAt: "2026-10-30T14:00:00Z",
    droppedAt: "2026-11-02T10:00:00Z",
  },
  {
    id: "cmp-vectorline-bench",
    clientId: "c-vectorline",
    status: "closed",
    title: "Search benchmark results",
    summary: "A thread walking through Vectorline's new benchmark and what it means for your stack.",
    brief: brief(
      "Vectorline makes search infrastructure for AI apps. They published an open benchmark of semantic search engines.",
      "Pick one result from the benchmark that surprised you and explain it in a short thread.",
      "Open numbers anyone can rerun, not marketing claims.",
    ),
    angles: ["The result that surprised you", "How to rerun it yourself", "What it changes for your stack"],
    deliverable: "thread",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://vectorline.example/bench?ref=agi2027" },
    requiredTags: { mentions: ["@vectorline"], hashtags: ["#SearchBench"], keywords: ["benchmark"] },
    assets: { brandKitUrl: "https://vectorline.example/press", files: [{ name: "benchmark-charts.png", kind: "image", sizeBytes: 2_300_000 }] },
    payout: { amount: "45000", currency: "NGN" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 10,
    slotsTaken: 7,
    requests: 0,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-10-28T14:00:00Z",
      postWindowEnd: "2026-10-29T14:00:00Z",
      claimDeadline: "2026-10-28T10:00:00Z",
      proofDeadline: "2026-10-30T12:00:00Z",
    },
    internal: { notes: "Closed early. The client had enough coverage.", budgetAmount: "450000", budgetCurrency: "NGN" },
    createdAt: "2026-10-20T09:00:00Z",
    droppedAt: "2026-10-22T09:00:00Z",
  },
  {
    id: "cmp-orbitar-alpha",
    clientId: "c-orbitar",
    status: "completed",
    title: "Private alpha first look",
    summary: "A 20 second screen recording of your first Orbitar prototype, with one line on how it felt.",
    brief: brief(
      "Orbitar turns rough sketches into clickable prototypes. This was the private alpha, before the public beta.",
      "Record your screen while Orbitar turns a sketch into a prototype. Keep it under 20 seconds.",
      "From napkin sketch to working prototype in one step.",
    ),
    angles: ["Your first prototype", "The moment it clicked"],
    deliverable: "video",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "https://orbitar.example/alpha?ref=agi2027" },
    requiredTags: { mentions: ["@orbitar"], hashtags: ["#OrbitarAlpha"], keywords: [] },
    assets: { brandKitUrl: "https://orbitar.example/press", files: [] },
    payout: { amount: "100", currency: "USD" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 6,
    slotsTaken: 5,
    requests: 0,
    audience: { kind: "tiers", tiers: ["Tier 2", "Tier 3"], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: true,
    paidLabelRequired: true,
    timing: {
      dropAt: "",
      postWindowStart: "2026-10-06T14:00:00Z",
      postWindowEnd: "2026-10-07T14:00:00Z",
      claimDeadline: "2026-10-06T10:00:00Z",
      proofDeadline: "2026-10-08T12:00:00Z",
    },
    internal: { notes: "The client renewed for the public beta.", budgetAmount: "600", budgetCurrency: "USD" },
    createdAt: "2026-09-28T10:00:00Z",
    droppedAt: "2026-10-01T09:00:00Z",
  },
];

/**
 * Who is on each campaign (the owner's roster view). Rows that hold a slot
 * (everything except requested, expired and cancelled) add up to the
 * campaign's slotsTaken.
 */
export const demoRosters: Record<string, DemoRosterRow[]> = {
  "cmp-nebula-2": [
    { creatorId: "u-amara", status: "claimed", angle: "The 10-minute build: show what you made", postTime: "2026-11-03T16:30:00Z", paid: false, at: "2026-10-30T15:02:00Z" },
    { creatorId: "u-theo", status: "proof_submitted", angle: "Why this matters for non-engineers", postTime: "2026-11-03T17:00:00Z", postUrl: "https://x.com/theoships/status/1975000000000000101", paid: false, at: "2026-11-03T17:12:00Z" },
    { creatorId: "u-lucia", status: "approved", angle: "Compare it to how you built agents last year", postTime: "2026-11-03T16:15:00Z", postUrl: "https://x.com/luciaferrer/status/1975000000000000102", views: 38200, paid: false, at: "2026-11-03T16:40:00Z" },
    { creatorId: "u-hana", status: "paid", angle: "The one feature you didn't expect", postTime: "2026-11-03T16:45:00Z", postUrl: "https://x.com/hanaonai/status/1975000000000000103", views: 21900, paid: true, at: "2026-11-03T18:05:00Z" },
    { creatorId: "u-kwame", status: "rejected", angle: "The 10-minute build: show what you made", postTime: "2026-11-03T18:00:00Z", postUrl: "https://x.com/kwamecodes/status/1975000000000000104", paid: false, at: "2026-11-03T18:20:00Z" },
    { creatorId: "u-jonah", status: "proof_submitted", angle: "The one feature you didn't expect", postTime: "2026-11-03T17:30:00Z", postUrl: "https://x.com/jonahreyes/status/1975000000000000105", paid: false, at: "2026-11-03T17:41:00Z" },
    { creatorId: "u-mei", status: "approved", angle: "The 10-minute build: show what you made", postTime: "2026-11-03T16:20:00Z", postUrl: "https://x.com/meilinai/status/1975000000000000106", views: 29400, paid: false, at: "2026-11-03T16:58:00Z" },
    { creatorId: "u-chidi", status: "paid", angle: "Why this matters for non-engineers", postTime: "2026-11-03T16:05:00Z", postUrl: "https://x.com/chidieze/status/1975000000000000107", views: 44100, paid: true, at: "2026-11-03T18:05:00Z" },
    { creatorId: "u-zara", status: "proof_submitted", angle: "Compare it to how you built agents last year", postTime: "2026-11-03T17:45:00Z", postUrl: "https://x.com/zarahaddad/status/1975000000000000108", paid: false, at: "2026-11-03T18:02:00Z" },
    { creatorId: "u-priya", status: "claimed", angle: "The 10-minute build: show what you made", postTime: "2026-11-03T19:00:00Z", paid: false, at: "2026-10-30T15:20:00Z" },
    { creatorId: "u-sofia", status: "claimed", angle: "Compare it to how you built agents last year", postTime: "2026-11-03T18:30:00Z", paid: false, at: "2026-10-30T16:01:00Z" },
    { creatorId: "u-ife", status: "claimed", paid: false, at: "2026-11-02T09:30:00Z" },
    { creatorId: "u-nadia", status: "claimed", paid: false, at: "2026-11-02T11:45:00Z" },
  ],
  "cmp-lumen-weights": [
    { creatorId: "u-priya", status: "requested", paid: false, at: "2026-11-01T08:10:00Z" },
    { creatorId: "u-dami", status: "requested", paid: false, at: "2026-11-01T13:25:00Z" },
    { creatorId: "u-marcus", status: "requested", paid: false, at: "2026-11-02T07:40:00Z" },
    { creatorId: "u-theo", status: "draft_submitted", angle: "Speed test on your laptop", paid: false, at: "2026-11-02T16:30:00Z" },
    { creatorId: "u-amara", status: "changes_requested", angle: "Privacy: nothing leaves the machine", paid: false, at: "2026-11-03T09:15:00Z" },
  ],
  "cmp-orbitar-beta": [
    { creatorId: "u-hana", status: "draft_approved", angle: "Before and after", postTime: "2026-11-07T15:00:00Z", paid: false, at: "2026-11-03T10:20:00Z" },
    { creatorId: "u-sofia", status: "draft_submitted", angle: "A real product idea you've had for years", paid: false, at: "2026-11-03T08:05:00Z" },
    { creatorId: "u-priya", status: "draft_submitted", angle: "Speedrun: sketch to prototype", paid: false, at: "2026-11-03T11:50:00Z" },
    { creatorId: "u-ana", status: "claimed", paid: false, at: "2026-11-02T09:00:00Z" },
    { creatorId: "u-mei", status: "changes_requested", angle: "Before and after", paid: false, at: "2026-11-03T12:30:00Z" },
    { creatorId: "u-lucia", status: "draft_approved", angle: "Speedrun: sketch to prototype", postTime: "2026-11-07T18:00:00Z", paid: false, at: "2026-11-02T17:45:00Z" },
    { creatorId: "u-zara", status: "claimed", angle: "A real product idea you've had for years", paid: false, at: "2026-11-01T19:30:00Z" },
    { creatorId: "u-oscar", status: "claimed", paid: false, at: "2026-11-02T22:10:00Z" },
    { creatorId: "u-jonah", status: "draft_submitted", angle: "Before and after", paid: false, at: "2026-11-03T14:40:00Z" },
    { creatorId: "u-leo", status: "cancelled", paid: false, at: "2026-11-02T12:00:00Z" },
  ],
  "cmp-vectorline-a": [
    { creatorId: "u-theo", status: "claimed", angle: "The problem in one example", postTime: "2026-11-04T13:30:00Z", paid: false, at: "2026-10-29T10:01:00Z" },
    { creatorId: "u-lucia", status: "claimed", angle: "What the raise unlocks", postTime: "2026-11-04T14:00:00Z", paid: false, at: "2026-10-29T10:01:00Z" },
    { creatorId: "u-jonah", status: "claimed", angle: "Who should try it this week", postTime: "2026-11-04T14:30:00Z", paid: false, at: "2026-10-29T10:02:00Z" },
    { creatorId: "u-mei", status: "claimed", angle: "The problem in one example", postTime: "2026-11-04T15:00:00Z", paid: false, at: "2026-10-29T10:02:00Z" },
    { creatorId: "u-chidi", status: "claimed", angle: "What the raise unlocks", postTime: "2026-11-04T13:15:00Z", paid: false, at: "2026-10-29T10:03:00Z" },
    { creatorId: "u-priya", status: "claimed", angle: "Who should try it this week", postTime: "2026-11-04T15:30:00Z", paid: false, at: "2026-10-29T10:03:00Z" },
    { creatorId: "u-kwame", status: "claimed", angle: "The problem in one example", postTime: "2026-11-04T16:30:00Z", paid: false, at: "2026-10-29T10:04:00Z" },
    { creatorId: "u-hana", status: "claimed", angle: "What the raise unlocks", postTime: "2026-11-04T14:15:00Z", paid: false, at: "2026-10-29T10:05:00Z" },
    { creatorId: "u-sofia", status: "claimed", angle: "Who should try it this week", postTime: "2026-11-04T16:00:00Z", paid: false, at: "2026-10-29T10:06:00Z" },
    { creatorId: "u-ife", status: "claimed", angle: "The problem in one example", postTime: "2026-11-04T15:45:00Z", paid: false, at: "2026-10-29T10:08:00Z" },
    { creatorId: "u-zara", status: "claimed", angle: "What the raise unlocks", postTime: "2026-11-04T13:45:00Z", paid: false, at: "2026-10-29T10:08:00Z" },
    { creatorId: "u-nadia", status: "claimed", paid: false, at: "2026-10-29T10:09:00Z" },
  ],
  "cmp-lumen-code": [
    { creatorId: "u-theo", status: "claimed", angle: "Your first hour, honestly", postTime: "2026-11-12T16:00:00Z", paid: false, at: "2026-11-02T10:01:00Z" },
    { creatorId: "u-kwame", status: "claimed", angle: "Working on a plane or a train", paid: false, at: "2026-11-02T10:03:00Z" },
    { creatorId: "u-oscar", status: "claimed", angle: "Privacy for client work", paid: false, at: "2026-11-02T10:12:00Z" },
    { creatorId: "u-jonah", status: "claimed", paid: false, at: "2026-11-02T11:30:00Z" },
  ],
  "cmp-vectorline-bench": [
    { creatorId: "u-dami", status: "paid", angle: "The result that surprised you", postTime: "2026-10-28T15:00:00Z", postUrl: "https://x.com/damiondata/status/1975000000000000301", views: 9100, paid: true, at: "2026-11-01T09:00:00Z" },
    { creatorId: "u-marcus", status: "approved", angle: "How to rerun it yourself", postTime: "2026-10-28T16:00:00Z", postUrl: "https://x.com/marcuswebb/status/1975000000000000302", views: 6800, paid: false, at: "2026-10-29T10:00:00Z" },
    { creatorId: "u-leo", status: "approved", angle: "What it changes for your stack", postTime: "2026-10-28T18:00:00Z", postUrl: "https://x.com/leomartins/status/1975000000000000303", views: 5200, paid: false, at: "2026-10-29T10:05:00Z" },
    { creatorId: "u-ana", status: "proof_submitted", angle: "The result that surprised you", postTime: "2026-10-29T12:00:00Z", postUrl: "https://x.com/anasouza/status/1975000000000000304", paid: false, at: "2026-10-29T13:10:00Z" },
    { creatorId: "u-nadia", status: "paid", angle: "How to rerun it yourself", postTime: "2026-10-28T14:30:00Z", postUrl: "https://x.com/nadiaprompt/status/1975000000000000305", views: 14100, paid: true, at: "2026-11-01T09:00:00Z" },
    { creatorId: "u-ife", status: "paid", angle: "What it changes for your stack", postTime: "2026-10-28T20:00:00Z", postUrl: "https://x.com/ifebuilds/status/1975000000000000306", views: 11900, paid: true, at: "2026-11-01T09:00:00Z" },
    { creatorId: "u-sofia", status: "approved", angle: "The result that surprised you", postTime: "2026-10-29T09:00:00Z", postUrl: "https://x.com/sofiaships/status/1975000000000000307", views: 13400, paid: false, at: "2026-10-29T11:30:00Z" },
    { creatorId: "u-oscar", status: "expired", paid: false, at: "2026-10-30T12:00:00Z" },
  ],
  "cmp-orbitar-alpha": [
    { creatorId: "u-hana", status: "paid", angle: "Your first prototype", postTime: "2026-10-06T15:00:00Z", postUrl: "https://x.com/hanaonai/status/1975000000000000401", views: 17600, paid: true, at: "2026-11-02T10:00:00Z" },
    { creatorId: "u-dami", status: "paid", angle: "The moment it clicked", postTime: "2026-10-06T17:00:00Z", postUrl: "https://x.com/damiondata/status/1975000000000000402", views: 7300, paid: true, at: "2026-11-02T10:00:00Z" },
    { creatorId: "u-kwame", status: "paid", angle: "Your first prototype", postTime: "2026-10-06T19:00:00Z", postUrl: "https://x.com/kwamecodes/status/1975000000000000403", views: 10400, paid: true, at: "2026-11-02T10:00:00Z" },
    { creatorId: "u-ana", status: "paid", angle: "The moment it clicked", postTime: "2026-10-07T09:00:00Z", postUrl: "https://x.com/anasouza/status/1975000000000000404", views: 5100, paid: true, at: "2026-11-02T10:00:00Z" },
    { creatorId: "u-leo", status: "paid", angle: "Your first prototype", postTime: "2026-10-07T11:00:00Z", postUrl: "https://x.com/leomartins/status/1975000000000000405", views: 4800, paid: true, at: "2026-11-02T10:00:00Z" },
    { creatorId: "u-marcus", status: "expired", paid: false, at: "2026-10-08T12:00:00Z" },
  ],
};

/** The demo creator's own claims (the creator's "My campaigns"). */
export const demoMyClaims: { campaignId: string; status: ClaimStatus; angle?: string; postTime?: string }[] = [
  { campaignId: "cmp-nebula-2", status: "claimed", angle: "The 10-minute build: show what you made", postTime: "2026-11-03T16:30:00Z" },
  { campaignId: "cmp-lumen-weights", status: "changes_requested", angle: "Privacy: nothing leaves the machine" },
];

export function clientById(id: string) {
  return demoClients.find((client) => client.id === id);
}

export function creatorById(id: string) {
  return demoCreators.find((creator) => creator.id === id);
}

export function campaignById(id: string) {
  return demoCampaigns.find((campaign) => campaign.id === id);
}

/** What one creator would be paid: their own amount, else their tier's, else the base. */
export function payoutFor(campaign: DemoCampaign, creator: DemoCreator) {
  const own = campaign.creatorPayouts.find((row) => row.creatorId === creator.id);
  if (own) return { amount: own.amount, currency: campaign.payout.currency };
  const tier = campaign.tierPayouts.find((row) => row.tier === creator.tier);
  if (tier) return { amount: tier.amount, currency: campaign.payout.currency };
  return campaign.payout;
}

/** Whether a creator is in a campaign's audience. */
export function canSee(campaign: DemoCampaign, creator: DemoCreator) {
  const { audience } = campaign;
  switch (audience.kind) {
    case "all":
      return true;
    case "tiers":
      return audience.tiers.includes(creator.tier);
    case "tags":
      return audience.tags.some((tag) => creator.tags.includes(tag));
    case "creators":
      return audience.creatorIds.includes(creator.id);
  }
}
