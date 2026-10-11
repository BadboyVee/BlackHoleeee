import { z } from "zod";

import type { ClaimMode, Platform } from "@/lib/campaigns/options";
import { totalsByCurrency } from "@/lib/money";
import type { CampaignStatus, ClaimStatus } from "@/lib/statuses";

/**
 * The creator side of the campaign loop as pure functions: slots, whether a
 * creator can claim, what happens next, proof links and calendar files.
 *
 * Nothing here reads the clock. Every rule that depends on time takes `now`,
 * so the browser preview, the database functions of Milestone 6 and the tests
 * all agree on the same answer for the same moment.
 */

type Instant = Date | number | string;

const MINUTE_MS = 60_000;
export const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

const toMs = (value: Instant) => (typeof value === "number" ? value : new Date(value).getTime());

/* ------------------------------------------------------------------ types */

export type ClaimTiming = {
  postWindowStart: string;
  postWindowEnd: string;
  claimDeadline: string;
  proofDeadline: string;
};

/** The parts of a campaign the claim rules need. */
export type ClaimableCampaign = {
  status: CampaignStatus;
  slots: number;
  slotsTaken: number;
  claimMode: ClaimMode;
  timing: ClaimTiming;
};

export type ClaimActor = "you" | "agency";

/** One step on a claim's timeline. Seeded history may have no time. */
export type ClaimEvent = { status: ClaimStatus; by: ClaimActor; at?: string; note?: string };

export type ClaimMedia = { name: string; kind: "image" | "video"; sizeBytes: number };

export type ClaimDraft = { text: string; media: ClaimMedia[]; submittedAt?: string };

export type ClaimProof = {
  url: string;
  handle: string;
  postId: string;
  screenshotName?: string;
  submittedAt?: string;
};

/** A creator's claim on one campaign, with its payout frozen at claim time. */
export type CreatorClaim = {
  campaignId: string;
  status: ClaimStatus;
  payout: { amount: string; currency: string };
  angle?: string;
  postTime?: string;
  /** The note sent with an apply-mode request. */
  note?: string;
  draft?: ClaimDraft;
  /** The agency's latest note: changes asked for, a rejection or a decline. */
  feedback?: string;
  proof?: ClaimProof;
  paidReference?: string;
  paidAt?: string;
  events: ClaimEvent[];
};

/* ------------------------------------------------------------- visibility */

/** Campaign statuses a creator in the audience can open. Drafts and scheduled drops stay hidden. */
export const CREATOR_VISIBLE_STATUSES: readonly CampaignStatus[] = ["live", "paused", "full", "closed", "completed"];

/** Campaign statuses that belong on the campaign board. */
export const BOARD_STATUSES: readonly CampaignStatus[] = ["live", "paused", "full"];

export function isVisibleToCreator(status: CampaignStatus, inAudience: boolean): boolean {
  return inAudience && CREATOR_VISIBLE_STATUSES.includes(status);
}

/* ------------------------------------------------------------------ slots */

/** Statuses that hold one of the campaign's slots (requests don't, dropped and expired claims give it back). */
export const SLOT_HOLDING_STATUSES: readonly ClaimStatus[] = [
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
  "proof_submitted",
  "approved",
  "rejected",
  "paid",
];

export function holdsSlot(status: ClaimStatus | null | undefined): boolean {
  return status ? SLOT_HOLDING_STATUSES.includes(status) : false;
}

export function slotsLeft(campaign: { slots: number; slotsTaken: number }): number {
  return Math.max(0, campaign.slots - campaign.slotsTaken);
}

/**
 * The campaign's taken slots once this creator's latest claim is counted. The
 * stored count already includes the claim the data started with (`seeded`),
 * so only the difference moves it.
 */
export function adjustSlotsTaken(
  slotsTaken: number,
  seeded: ClaimStatus | null | undefined,
  current: ClaimStatus | null | undefined,
): number {
  const before = holdsSlot(seeded) ? 1 : 0;
  const after = holdsSlot(current) ? 1 : 0;
  return Math.max(0, slotsTaken - before + after);
}

/** Live and Full switch automatically as slots fill up or reopen. */
export function liveStatus(status: CampaignStatus, left: number): CampaignStatus {
  if (status === "live" && left === 0) return "full";
  if (status === "full" && left > 0) return "live";
  return status;
}

/* ------------------------------------------------------------ claiming */

export type ClaimAvailabilityState =
  | "instant"
  | "apply"
  | "already_claimed"
  | "not_in_audience"
  | "not_open"
  | "paused"
  | "closed"
  | "deadline_passed"
  | "full";

export type ClaimAvailability = {
  state: ClaimAvailabilityState;
  canClaim: boolean;
  title: string;
  detail: string;
};

/**
 * Whether one creator can claim a campaign right now, and why not if they
 * can't. Checked in order: their own claim, the audience, the campaign's
 * status, the claim deadline, free slots, then the claim mode.
 */
export function claimAvailability({
  campaign,
  now,
  inAudience,
  claim,
}: {
  campaign: ClaimableCampaign;
  now: Instant;
  inAudience: boolean;
  claim?: { status: ClaimStatus } | null;
}): ClaimAvailability {
  if (claim) {
    const copy: Partial<Record<ClaimStatus, [string, string]>> = {
      requested: ["Request sent", "Waiting for the agency. Requests don't hold a slot, so keep an eye on your notifications."],
      cancelled: ["You left this one", "Each campaign can be claimed once, so this one can't be claimed again."],
      expired: ["This claim expired", "The proof deadline passed and the slot went back to the pool."],
    };
    const [title, detail] = copy[claim.status] ?? ["You're in", "You hold a slot on this campaign."];
    return { state: "already_claimed", canClaim: false, title, detail };
  }
  if (!inAudience) {
    return {
      state: "not_in_audience",
      canClaim: false,
      title: "Not open to you",
      detail: "This campaign is meant for a different group of creators.",
    };
  }
  if (campaign.status === "draft" || campaign.status === "scheduled") {
    return { state: "not_open", canClaim: false, title: "Not open yet", detail: "It opens to creators the moment it drops." };
  }
  if (campaign.status === "paused") {
    return {
      state: "paused",
      canClaim: false,
      title: "Paused for now",
      detail: "The agency paused new claims. Check back soon.",
    };
  }
  if (campaign.status === "closed" || campaign.status === "completed") {
    return { state: "closed", canClaim: false, title: "Claiming closed", detail: "This campaign isn't taking new claims." };
  }
  if (toMs(now) >= toMs(campaign.timing.claimDeadline)) {
    return {
      state: "deadline_passed",
      canClaim: false,
      title: "Claiming closed",
      detail: "The claim deadline has passed, so no new claims can come in.",
    };
  }
  if (campaign.status === "full" || slotsLeft(campaign) === 0) {
    return {
      state: "full",
      canClaim: false,
      title: "Full",
      detail: "Every slot is taken. A slot reopens if someone drops out.",
    };
  }
  return campaign.claimMode === "instant"
    ? {
        state: "instant",
        canClaim: true,
        title: "Claim a slot",
        detail: "First come, first served. Your slot is held the moment you confirm.",
      }
    : {
        state: "apply",
        canClaim: true,
        title: "Request to join",
        detail: "Send a short note. The agency picks the creators for this one.",
      };
}

/** The rules creators agree to when they claim. */
export const CLAIM_RULES = [
  "One claim per campaign.",
  "You can drop it before your post window starts, and the slot reopens.",
  "Proof is due by the deadline, or the slot reopens.",
] as const;

/* ------------------------------------------------------------ the loop */

/** Every allowed move, from PLAN.md. Draft states only apply when a draft is required. */
export const CLAIM_TRANSITIONS: Record<ClaimStatus, readonly ClaimStatus[]> = {
  requested: ["claimed", "cancelled"],
  claimed: ["draft_submitted", "proof_submitted", "cancelled", "expired"],
  draft_submitted: ["draft_approved", "changes_requested", "cancelled", "expired"],
  changes_requested: ["draft_submitted", "cancelled", "expired"],
  draft_approved: ["proof_submitted", "cancelled", "expired"],
  proof_submitted: ["approved", "rejected"],
  rejected: ["proof_submitted", "expired"],
  approved: ["paid"],
  paid: [],
  expired: [],
  cancelled: [],
};

export function canMoveClaim(from: ClaimStatus, to: ClaimStatus, { draftRequired }: { draftRequired: boolean }): boolean {
  if (!CLAIM_TRANSITIONS[from].includes(to)) return false;
  if (from === "claimed" && to === "draft_submitted") return draftRequired;
  if (from === "claimed" && to === "proof_submitted") return !draftRequired;
  return true;
}

/** The steps a claim moves through on one campaign, in order. */
export function claimPath({ claimMode, draftRequired }: { claimMode: ClaimMode; draftRequired: boolean }): ClaimStatus[] {
  return [
    ...(claimMode === "apply" ? (["requested"] as const) : []),
    "claimed",
    ...(draftRequired ? (["draft_submitted", "draft_approved"] as const) : []),
    "proof_submitted",
    "approved",
    "paid",
  ];
}

/**
 * The furthest step a claim has reached on its path. Changes requested and
 * rejected proof sit on the step they send you back to. -1 once a claim has
 * stopped (dropped, declined or expired).
 */
export function pathPosition(path: readonly ClaimStatus[], status: ClaimStatus): number {
  if (status === "expired" || status === "cancelled") return -1;
  if (status === "changes_requested") return path.indexOf("draft_submitted");
  if (status === "rejected") return path.indexOf("proof_submitted");
  return Math.max(0, path.indexOf(status));
}

/** Claims that expire if no proof is in by the proof deadline. */
export const EXPIRES_WITHOUT_PROOF: readonly ClaimStatus[] = [
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
  "rejected",
];

/**
 * What the scheduler does at the deadlines, applied when reading claims: no
 * proof by the proof deadline means expired (the slot reopens), and a request
 * still waiting when claiming closes is declined. Proof already submitted
 * never expires.
 */
export function applyDeadlines(claim: CreatorClaim, timing: ClaimTiming, now: Instant): CreatorClaim {
  const t = toMs(now);
  if (EXPIRES_WITHOUT_PROOF.includes(claim.status) && t >= toMs(timing.proofDeadline)) {
    return {
      ...claim,
      status: "expired",
      events: [
        ...claim.events,
        {
          status: "expired",
          by: "agency",
          at: timing.proofDeadline,
          note: "No proof came in before the deadline, so the slot went back to the pool.",
        },
      ],
    };
  }
  if (claim.status === "requested" && t >= toMs(timing.claimDeadline)) {
    return {
      ...claim,
      status: "cancelled",
      events: [
        ...claim.events,
        { status: "cancelled", by: "agency", at: timing.claimDeadline, note: "Claiming closed before your request was accepted." },
      ],
    };
  }
  return claim;
}

/** Claims a creator can still walk away from (a pending request can be withdrawn too). */
export const DROPPABLE_STATUSES: readonly ClaimStatus[] = [
  "requested",
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
];

/** A claim can be dropped until the post window starts. */
export function canDropClaim(status: ClaimStatus, timing: Pick<ClaimTiming, "postWindowStart">, now: Instant): boolean {
  return DROPPABLE_STATUSES.includes(status) && toMs(now) < toMs(timing.postWindowStart);
}

export type NextStep = {
  title: string;
  detail: string;
  /** Who moves next, or null once the claim is settled. */
  actor: ClaimActor | null;
};

/** What happens next for a claim, in the creator's words. */
export function nextStep(status: ClaimStatus, { draftRequired }: { draftRequired: boolean }): NextStep {
  switch (status) {
    case "requested":
      return {
        title: "Waiting for the agency",
        detail: "Your request doesn't hold a slot yet. You'll hear back as soon as the agency decides.",
        actor: "agency",
      };
    case "claimed":
      return draftRequired
        ? {
            title: "Write your draft",
            detail: "Send your draft for a quick check. Once it's approved, post it inside your window.",
            actor: "you",
          }
        : {
            title: "Post inside your window",
            detail: "Post it during your window, then paste the link here as proof.",
            actor: "you",
          };
    case "draft_submitted":
      return { title: "Draft in review", detail: "The agency is reading your draft. You'll hear back here.", actor: "agency" };
    case "changes_requested":
      return {
        title: "Update your draft",
        detail: "Read the agency's note, edit your draft and send it again.",
        actor: "you",
      };
    case "draft_approved":
      return {
        title: "Post it",
        detail: "Your draft is approved. Post it inside your window, then paste the link here.",
        actor: "you",
      };
    case "proof_submitted":
      return { title: "Proof in review", detail: "The agency is checking your post. Nothing to do for now.", actor: "agency" };
    case "approved":
      return {
        title: "Payment on the way",
        detail: "Your post is approved. The payment shows as Unpaid in Earnings until it's sent.",
        actor: "agency",
      };
    case "rejected":
      return {
        title: "Fix your post",
        detail: "Read the agency's note, fix the post and send the link again before the proof deadline.",
        actor: "you",
      };
    case "paid":
      return { title: "Paid", detail: "All done. The payment reference is in Earnings.", actor: null };
    case "expired":
      return { title: "Expired", detail: "The proof deadline passed and the slot went back to the pool.", actor: null };
    case "cancelled":
      return { title: "Dropped", detail: "This claim was dropped or declined, so it's closed.", actor: null };
  }
}

/** The countdown that matters most for a claim right now, or null when nothing is ticking. */
export function claimClock(
  status: ClaimStatus,
  timing: ClaimTiming,
  now: Instant,
): { label: string; to: string } | null {
  const t = toMs(now);
  if (status === "requested") {
    return t < toMs(timing.claimDeadline) ? { label: "Claiming closes in", to: timing.claimDeadline } : null;
  }
  if (status === "rejected") {
    return t < toMs(timing.proofDeadline) ? { label: "Proof due in", to: timing.proofDeadline } : null;
  }
  if (!["claimed", "draft_submitted", "changes_requested", "draft_approved"].includes(status)) return null;
  if (t < toMs(timing.postWindowStart)) return { label: "Window opens in", to: timing.postWindowStart };
  if (t < toMs(timing.postWindowEnd)) return { label: "Window closes in", to: timing.postWindowEnd };
  if (t < toMs(timing.proofDeadline)) return { label: "Proof due in", to: timing.proofDeadline };
  return null;
}

export type AttentionKind = "changes_requested" | "rejected" | "proof_due" | "draft_due" | "window_soon";

/** Whether a claim needs the creator now, and why. */
export function attentionFor(
  status: ClaimStatus,
  timing: ClaimTiming,
  now: Instant,
  { draftRequired }: { draftRequired: boolean },
): AttentionKind | null {
  const t = toMs(now);
  const start = toMs(timing.postWindowStart);
  if (status === "changes_requested") return "changes_requested";
  if (status === "rejected") return t < toMs(timing.proofDeadline) ? "rejected" : null;
  if (status === "claimed" && draftRequired) return start - t <= 2 * DAY_MS && t < toMs(timing.proofDeadline) ? "draft_due" : null;
  if (status === "claimed" || status === "draft_approved") {
    if (t >= start && t < toMs(timing.proofDeadline)) return "proof_due";
    if (t < start && start - t <= DAY_MS) return "window_soon";
  }
  return null;
}

/* ---------------------------------------------------------- my campaigns */

export const MY_CAMPAIGN_TABS = ["active", "submitted", "approved", "paid", "past"] as const;
export type MyCampaignTab = (typeof MY_CAMPAIGN_TABS)[number];

export const myCampaignTabMeta: Record<MyCampaignTab, { label: string; empty: string; hint: string }> = {
  active: {
    label: "Active",
    empty: "Nothing on your plate",
    hint: "Claim a campaign and it shows up here while you draft and post.",
  },
  submitted: {
    label: "Submitted",
    empty: "Nothing waiting on the agency",
    hint: "Requests, drafts and proof you send land here until the agency replies.",
  },
  approved: {
    label: "Approved",
    empty: "No approvals yet",
    hint: "Approved posts wait here until the payment goes out.",
  },
  paid: { label: "Paid", empty: "No payments yet", hint: "Paid campaigns show up here with their payment reference." },
  past: { label: "Past", empty: "No past campaigns", hint: "Dropped and expired claims end up here." },
};

/** Which My campaigns tab a claim belongs in. */
export function myCampaignTab(status: ClaimStatus): MyCampaignTab {
  switch (status) {
    case "requested":
    case "draft_submitted":
    case "proof_submitted":
      return "submitted";
    case "approved":
      return "approved";
    case "paid":
      return "paid";
    case "expired":
    case "cancelled":
      return "past";
    default:
      return "active";
  }
}

/* -------------------------------------------------------------- earnings */

export type EarningRow = {
  campaignId: string;
  amount: string;
  currency: string;
  status: "unpaid" | "paid";
  reference?: string;
  paidAt?: string;
};

/** Approved claims earn an Unpaid earning; paid claims carry their reference. */
export function earningsFromClaims(claims: readonly CreatorClaim[]): EarningRow[] {
  return claims
    .filter((claim) => claim.status === "approved" || claim.status === "paid")
    .map((claim) => ({
      campaignId: claim.campaignId,
      amount: claim.payout.amount,
      currency: claim.payout.currency,
      status: claim.status === "paid" ? "paid" : "unpaid",
      reference: claim.paidReference,
      paidAt: claim.paidAt,
    }));
}

/** Totals per currency. USD and NGN are never added together. */
export function earningsSummary(rows: readonly EarningRow[]) {
  return {
    unpaid: totalsByCurrency(rows.filter((row) => row.status === "unpaid")),
    paid: totalsByCurrency(rows.filter((row) => row.status === "paid")),
    total: totalsByCurrency([...rows]),
  };
}

/* ---------------------------------------------------------------- board */

export type DateBucket = "today" | "week" | "later";

const dayFormatters = new Map<string, Intl.DateTimeFormat>();

/** Days since 1970 for the calendar date in a time zone (the viewer's by default). */
function calendarDay(value: Instant, timeZone?: string): number {
  const key = timeZone ?? "local";
  let formatter = dayFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat("en-US", { year: "numeric", month: "numeric", day: "numeric", timeZone });
    dayFormatters.set(key, formatter);
  }
  const parts: Record<string, number> = {};
  for (const part of formatter.formatToParts(new Date(toMs(value)))) parts[part.type] = Number(part.value);
  return Math.round(Date.UTC(parts.year, parts.month - 1, parts.day) / DAY_MS);
}

/** Today (including windows already running), within the next 7 days, or later. */
export function dateBucket(start: Instant, now: Instant, timeZone?: string): DateBucket {
  const days = calendarDay(start, timeZone) - calendarDay(now, timeZone);
  if (days <= 0) return "today";
  if (days <= 7) return "week";
  return "later";
}

/** How long a drop counts as new. */
export const NEW_DROP_MS = 72 * HOUR_MS;

export function isNewDrop(droppedAt: Instant, now: Instant): boolean {
  return toMs(now) - toMs(droppedAt) < NEW_DROP_MS;
}

export type BoardSort = "newest" | "payout" | "ending";

/** Stablecoins track the dollar, so they compare with USD; other currencies compare among themselves. */
const DOLLAR_LIKE = new Set(["USD", "USDC", "USDT"]);

type Sortable = { droppedAt: string; payout: { amount: string; currency: string }; timing: Pick<ClaimTiming, "claimDeadline"> };

/**
 * Sorts board campaigns. "payout" never converts currencies: dollar amounts
 * come first, highest first, then each other currency on its own.
 */
export function sortCampaigns<T extends Sortable>(list: readonly T[], sort: BoardSort, now: Instant): T[] {
  const t = toMs(now);
  const copy = [...list];
  if (sort === "newest") return copy.sort((a, b) => toMs(b.droppedAt) - toMs(a.droppedAt));
  if (sort === "ending") {
    return copy.sort((a, b) => {
      const aLeft = toMs(a.timing.claimDeadline) - t;
      const bLeft = toMs(b.timing.claimDeadline) - t;
      if (aLeft > 0 !== bLeft > 0) return aLeft > 0 ? -1 : 1;
      return aLeft > 0 ? aLeft - bLeft : bLeft - aLeft;
    });
  }
  const group = (currency: string) => (DOLLAR_LIKE.has(currency) ? "" : currency);
  return copy.sort((a, b) => {
    const ga = group(a.payout.currency);
    const gb = group(b.payout.currency);
    if (ga !== gb) return ga.localeCompare(gb);
    return Number(b.payout.amount) - Number(a.payout.amount);
  });
}

/* ------------------------------------------------------------ proof links */

export type PostRef = { handle: string; postId: string };

const X_HOSTS = new Set(["x.com", "www.x.com", "mobile.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"]);
const HANDLE = /^[A-Za-z0-9_]{1,15}$/;
/** Paths on X that look like a handle but aren't one. */
const RESERVED_PATHS = new Set(["i", "home", "explore", "search", "settings", "intent", "share", "hashtag"]);

function toUrl(input: string): URL | null {
  let text = input.trim();
  if (!text || /\s/.test(text)) return null;
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(text)) text = `https://${text}`;
  try {
    const url = new URL(text);
    return url.protocol === "https:" || url.protocol === "http:" ? url : null;
  } catch {
    return null;
  }
}

/**
 * Reads the author and post ID from an X link. Accepts x.com, twitter.com and
 * the mobile hosts, with or without https and tracking query strings, and
 * extra segments like /photo/1. Returns null for anything that isn't a post.
 */
export function parseXPostUrl(input: string): PostRef | null {
  const url = toUrl(input);
  if (!url || url.username || url.password) return null;
  if (!X_HOSTS.has(url.hostname.toLowerCase())) return null;
  const [handle, kind, postId] = url.pathname.split("/").filter(Boolean);
  if (!handle || !HANDLE.test(handle) || RESERVED_PATHS.has(handle.toLowerCase())) return null;
  if (kind !== "status" && kind !== "statuses") return null;
  if (!postId || !/^\d{1,20}$/.test(postId)) return null;
  return { handle, postId };
}

/** The one canonical form of an X post link, without tracking: https://x.com/handle/status/id. */
export function normalizeXPostUrl(input: string): string | null {
  const post = parseXPostUrl(input);
  return post ? `https://x.com/${post.handle}/status/${post.postId}` : null;
}

/** Handles match without the @ and regardless of case. */
export function sameHandle(a: string, b: string): boolean {
  const clean = (value: string) => value.trim().replace(/^@/, "").toLowerCase();
  return clean(a) !== "" && clean(a) === clean(b);
}

const PLATFORM_POST: Record<Exclude<Platform, "x">, { hosts: string[]; path: RegExp }> = {
  tiktok: { hosts: ["tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com"], path: /^\/(@[\w.]+\/video\/\d+|[A-Za-z0-9]+\/?$)/ },
  instagram: { hosts: ["instagram.com", "www.instagram.com"], path: /^\/(p|reel|reels)\/[\w-]+/ },
  linkedin: { hosts: ["linkedin.com", "www.linkedin.com"], path: /^\/(posts|feed\/update)\// },
  youtube: { hosts: ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"], path: /^\/(watch|shorts\/[\w-]+|[\w-]{6,})/ },
};

export type ProofCheck = { id: "link" | "handle"; ok: boolean; label: string };

export type ProofLinkResult = {
  ok: boolean;
  checks: ProofCheck[];
  /** The link as it will be saved, tracking stripped. */
  normalized: string | null;
  post: PostRef | null;
};

/**
 * The free checks a proof link gets before it's sent: a real post link for
 * the campaign's platform and, on X, the creator's own handle.
 */
export function checkProofLink(input: string, { platform, handle }: { platform: Platform; handle: string }): ProofLinkResult {
  const platformName = { x: "X", tiktok: "TikTok", instagram: "Instagram", linkedin: "LinkedIn", youtube: "YouTube" }[platform];
  if (platform === "x") {
    const post = parseXPostUrl(input);
    const linkCheck: ProofCheck = post
      ? { id: "link", ok: true, label: "A real X post link" }
      : { id: "link", ok: false, label: "Paste a link like x.com/you/status/123" };
    const own = post ? sameHandle(post.handle, handle) : false;
    const handleCheck: ProofCheck = post
      ? own
        ? { id: "handle", ok: true, label: `Posted from @${handle.replace(/^@/, "")}` }
        : { id: "handle", ok: false, label: `This post is from @${post.handle}, not @${handle.replace(/^@/, "")}` }
      : { id: "handle", ok: false, label: `Posted from @${handle.replace(/^@/, "")}` };
    return {
      ok: Boolean(post) && own,
      checks: [linkCheck, handleCheck],
      normalized: post ? `https://x.com/${post.handle}/status/${post.postId}` : null,
      post,
    };
  }
  const url = toUrl(input);
  const rule = PLATFORM_POST[platform];
  const ok = Boolean(url && rule.hosts.includes(url.hostname.toLowerCase()) && rule.path.test(url.pathname));
  let normalized: string | null = null;
  if (ok && url) {
    const video = platform === "youtube" ? url.searchParams.get("v") : null;
    normalized = `https://${url.hostname.toLowerCase()}${url.pathname.replace(/\/$/, "")}${video ? `?v=${video}` : ""}`;
  }
  return {
    ok,
    checks: [
      ok
        ? { id: "link", ok: true, label: `A real ${platformName} post link` }
        : { id: "link", ok: false, label: `Paste the link to your ${platformName} post` },
    ],
    normalized,
    post: null,
  };
}

/* ------------------------------------------------------------------ forms */

export const REQUEST_NOTE_MIN = 10;
export const REQUEST_NOTE_MAX = 500;

export const requestNoteSchema = z.object({
  note: z
    .string()
    .trim()
    .min(REQUEST_NOTE_MIN, `Write at least ${REQUEST_NOTE_MIN} characters`)
    .max(REQUEST_NOTE_MAX, `Keep it under ${REQUEST_NOTE_MAX} characters`),
});
export type RequestNoteValues = z.infer<typeof requestNoteSchema>;

export const draftSchema = z.object({
  text: z
    .string()
    .trim()
    .min(20, "Write at least 20 characters so the agency can judge it")
    .max(5000, "Keep it under 5,000 characters"),
});
export type DraftValues = z.infer<typeof draftSchema>;

export function makeProofSchema({ platform, handle }: { platform: Platform; handle: string }) {
  return z.object({
    url: z
      .string()
      .trim()
      .min(1, "Paste the link to your post")
      .superRefine((value, ctx) => {
        const failed = checkProofLink(value, { platform, handle }).checks.find((check) => !check.ok);
        if (failed) ctx.addIssue({ code: "custom", message: failed.label });
      }),
    labelUsed: z.boolean().refine((value) => value, "Confirm you used the paid partnership label"),
    briefFollowed: z.boolean().refine((value) => value, "Confirm you followed the brief"),
  });
}
export type ProofValues = z.infer<ReturnType<typeof makeProofSchema>>;

/** The required tags that appear in a piece of text, matched without case. */
export function tagsFound(text: string, tags: readonly string[]): Record<string, boolean> {
  const haystack = text.toLowerCase();
  return Object.fromEntries(tags.map((tag) => [tag, haystack.includes(tag.toLowerCase())]));
}

/* --------------------------------------------------------------- calendar */

export type CalendarEvent = {
  uid: string;
  title: string;
  start: string;
  end: string;
  description?: string;
  url?: string;
  /** Adds a reminder this many minutes before the start. */
  alarmMinutesBefore?: number;
};

/** "20261103T160000Z": the UTC form calendar files use. */
export function icsTimestamp(value: Instant): string {
  return new Date(toMs(value)).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

/** Escapes text for an ICS property value (RFC 5545, 3.3.11). */
export function escapeIcsText(text: string): string {
  return text.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

/** Folds a content line at 75 bytes, continuing with a space (RFC 5545, 3.1). */
export function foldIcsLine(line: string): string {
  const encoder = new TextEncoder();
  const out: string[] = [];
  let current = "";
  let bytes = 0;
  for (const char of line) {
    const size = encoder.encode(char).length;
    const limit = out.length === 0 ? 75 : 74;
    if (bytes + size > limit) {
      out.push(current);
      current = "";
      bytes = 0;
    }
    current += char;
    bytes += size;
  }
  out.push(current);
  return out.join("\r\n ");
}

/** A calendar file with one event per entry, ready to download. */
export function buildIcs(events: readonly CalendarEvent[], now: Instant): string {
  const stamp = icsTimestamp(now);
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AGI 2027//Creator portal//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"];
  for (const event of events) {
    lines.push(
      "BEGIN:VEVENT",
      `UID:${event.uid}`,
      `DTSTAMP:${stamp}`,
      `DTSTART:${icsTimestamp(event.start)}`,
      `DTEND:${icsTimestamp(event.end)}`,
      `SUMMARY:${escapeIcsText(event.title)}`,
    );
    if (event.description) lines.push(`DESCRIPTION:${escapeIcsText(event.description)}`);
    if (event.url) lines.push(`URL:${event.url}`);
    if (event.alarmMinutesBefore !== undefined) {
      lines.push(
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        `DESCRIPTION:${escapeIcsText(event.title)}`,
        `TRIGGER:-PT${Math.max(0, Math.round(event.alarmMinutesBefore))}M`,
        "END:VALARM",
      );
    }
    lines.push("END:VEVENT");
  }
  lines.push("END:VCALENDAR");
  return `${lines.map(foldIcsLine).join("\r\n")}\r\n`;
}
