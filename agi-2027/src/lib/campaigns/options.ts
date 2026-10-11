/**
 * The fixed choices a campaign is built from. Labels live here so the builder,
 * the creator board, filters and emails always say the same thing.
 */

export const PLATFORMS = ["x", "tiktok", "instagram", "linkedin", "youtube"] as const;
export type Platform = (typeof PLATFORMS)[number];

export const platformLabel: Record<Platform, string> = {
  x: "X",
  tiktok: "TikTok",
  instagram: "Instagram",
  linkedin: "LinkedIn",
  youtube: "YouTube",
};

export const DELIVERABLES = ["original", "quote", "reply", "thread", "video", "other"] as const;
export type Deliverable = (typeof DELIVERABLES)[number];

export const deliverableMeta: Record<Deliverable, { label: string; hint: string }> = {
  original: { label: "Original post", hint: "A new post in the creator's own words." },
  quote: { label: "Quote post", hint: "Quotes a post you choose, with the creator's take on top." },
  reply: { label: "Reply", hint: "Replies under a post you choose." },
  thread: { label: "Thread", hint: "Several connected posts that tell a fuller story." },
  video: { label: "Video", hint: "A short clip, posted natively." },
  other: { label: "Other", hint: "Anything else. Explain it in the brief." },
};

/** Deliverables that need a target post to quote or reply to. */
export const NEEDS_TARGET_POST: ReadonlySet<Deliverable> = new Set(["quote", "reply"]);

export const CLAIM_MODES = ["instant", "apply"] as const;
export type ClaimMode = (typeof CLAIM_MODES)[number];

export const claimModeMeta: Record<ClaimMode, { label: string; hint: string }> = {
  instant: {
    label: "Instant",
    hint: "First come, first served. Tapping Claim reserves a slot straight away.",
  },
  apply: {
    label: "Apply",
    hint: "Creators send a short note. You accept each request from the review queue.",
  },
};

export const AUDIENCE_KINDS = ["all", "tiers", "tags", "creators"] as const;
export type AudienceKind = (typeof AUDIENCE_KINDS)[number];

export const audienceMeta: Record<AudienceKind, { label: string; hint: string }> = {
  all: { label: "All creators", hint: "Every approved creator sees it." },
  tiers: { label: "Chosen tiers", hint: "Only creators in the tiers you pick." },
  tags: { label: "Chosen tags", hint: "Only creators with at least one of the tags you pick." },
  creators: { label: "Hand-picked", hint: "Only the creators you choose by name." },
};

/** Starting list; editable in Settings later (Milestone 9). */
export const CURRENCIES = ["USD", "USDC", "USDT", "NGN"] as const;
export type Currency = (typeof CURRENCIES)[number];

export const TIERS = ["Tier 1", "Tier 2", "Tier 3"] as const;
export type Tier = (typeof TIERS)[number];

export const CREATOR_TAGS = ["AI builders", "Crypto", "Startups", "Design", "Dev tools", "Founders"] as const;

export const ASSET_KINDS = ["image", "video", "document"] as const;
export type AssetKind = (typeof ASSET_KINDS)[number];

/** How the campaign goes out when the owner saves it. */
export const publishMeta: Record<"draft" | "now" | "schedule", { label: string; hint: string; action: string }> = {
  draft: {
    label: "Save as draft",
    hint: "Only your team can see it. Publish or schedule it later.",
    action: "Save draft",
  },
  now: {
    label: "Publish now",
    hint: "It drops the moment you save. Creators are notified straight away.",
    action: "Publish now",
  },
  schedule: {
    label: "Schedule a drop time",
    hint: "It stays private until the time you pick, then drops on its own.",
    action: "Schedule drop",
  },
};
