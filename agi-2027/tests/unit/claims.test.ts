import { describe, expect, it } from "vitest";

import {
  adjustSlotsTaken,
  applyDeadlines,
  attentionFor,
  buildIcs,
  canDropClaim,
  canMoveClaim,
  checkProofLink,
  claimPath,
  claimAvailability,
  claimClock,
  dateBucket,
  earningsFromClaims,
  earningsSummary,
  escapeIcsText,
  foldIcsLine,
  icsTimestamp,
  isNewDrop,
  isVisibleToCreator,
  liveStatus,
  makeProofSchema,
  myCampaignTab,
  nextStep,
  normalizeXPostUrl,
  parseXPostUrl,
  pathPosition,
  requestNoteSchema,
  sameHandle,
  slotsLeft,
  sortCampaigns,
  tagsFound,
  type ClaimableCampaign,
  type CreatorClaim,
} from "@/lib/campaigns/claims";
import { CLAIM_STATUSES } from "@/lib/statuses";

/** Every test runs at this moment: a Sunday morning, a few days before the window. */
const NOW = new Date("2026-11-01T09:00:00Z");

const timing = {
  postWindowStart: "2026-11-03T16:00:00Z",
  postWindowEnd: "2026-11-03T20:00:00Z",
  claimDeadline: "2026-11-03T14:00:00Z",
  proofDeadline: "2026-11-04T12:00:00Z",
};

const campaign = (overrides: Partial<ClaimableCampaign> = {}): ClaimableCampaign => ({
  status: "live",
  slots: 20,
  slotsTaken: 13,
  claimMode: "instant",
  timing,
  ...overrides,
});

const at = (iso: string) => new Date(iso);

describe("slots", () => {
  it("counts the slots that are still free", () => {
    expect(slotsLeft({ slots: 20, slotsTaken: 13 })).toBe(7);
    expect(slotsLeft({ slots: 12, slotsTaken: 12 })).toBe(0);
  });

  it("never goes below zero, even if a campaign was overfilled", () => {
    expect(slotsLeft({ slots: 5, slotsTaken: 7 })).toBe(0);
  });

  it("moves the count only when this creator's claim starts or stops holding a slot", () => {
    expect(adjustSlotsTaken(13, undefined, "claimed")).toBe(14);
    expect(adjustSlotsTaken(13, "claimed", "cancelled")).toBe(12);
    expect(adjustSlotsTaken(13, "claimed", "proof_submitted")).toBe(13);
    expect(adjustSlotsTaken(13, undefined, "requested")).toBe(13);
    expect(adjustSlotsTaken(2, "requested", "claimed")).toBe(3);
    expect(adjustSlotsTaken(0, "claimed", "expired")).toBe(0);
  });

  it("switches between Live and Full as slots fill up and reopen", () => {
    expect(liveStatus("live", 0)).toBe("full");
    expect(liveStatus("full", 1)).toBe("live");
    expect(liveStatus("live", 3)).toBe("live");
    expect(liveStatus("closed", 0)).toBe("closed");
  });
});

describe("isVisibleToCreator", () => {
  it("hides drafts and scheduled drops, and anything outside the audience", () => {
    expect(isVisibleToCreator("live", true)).toBe(true);
    expect(isVisibleToCreator("completed", true)).toBe(true);
    expect(isVisibleToCreator("draft", true)).toBe(false);
    expect(isVisibleToCreator("scheduled", true)).toBe(false);
    expect(isVisibleToCreator("live", false)).toBe(false);
  });
});

describe("claimAvailability", () => {
  const check = (overrides: Partial<ClaimableCampaign> = {}, extra: { inAudience?: boolean; now?: Date } = {}) =>
    claimAvailability({ campaign: campaign(overrides), now: extra.now ?? NOW, inAudience: extra.inAudience ?? true });

  it("lets an audience member claim an instant campaign straight away", () => {
    expect(check()).toMatchObject({ state: "instant", canClaim: true });
  });

  it("asks for a request on an apply campaign", () => {
    expect(check({ claimMode: "apply" })).toMatchObject({ state: "apply", canClaim: true });
  });

  it("is full when the status says so or no slot is left", () => {
    expect(check({ status: "full", slotsTaken: 20 })).toMatchObject({ state: "full", canClaim: false });
    expect(check({ slotsTaken: 20 })).toMatchObject({ state: "full", canClaim: false });
    expect(check({ claimMode: "apply", slotsTaken: 20 })).toMatchObject({ state: "full" });
  });

  it("is closed for closed and completed campaigns", () => {
    expect(check({ status: "closed" })).toMatchObject({ state: "closed", canClaim: false });
    expect(check({ status: "completed" })).toMatchObject({ state: "closed", canClaim: false });
  });

  it("is paused while the agency pauses claims", () => {
    expect(check({ status: "paused" })).toMatchObject({ state: "paused", canClaim: false });
  });

  it("closes at the claim deadline, to the second", () => {
    expect(check({}, { now: at("2026-11-03T13:59:59Z") }).canClaim).toBe(true);
    expect(check({}, { now: at("2026-11-03T14:00:00Z") })).toMatchObject({ state: "deadline_passed", canClaim: false });
  });

  it("says a passed deadline before saying full", () => {
    expect(check({ slotsTaken: 20 }, { now: at("2026-11-03T15:00:00Z") }).state).toBe("deadline_passed");
  });

  it("refuses creators outside the audience", () => {
    expect(check({}, { inAudience: false })).toMatchObject({ state: "not_in_audience", canClaim: false });
  });

  it("isn't open before the campaign drops", () => {
    expect(check({ status: "scheduled" }).state).toBe("not_open");
    expect(check({ status: "draft" }).state).toBe("not_open");
  });

  it("allows one claim per campaign, whatever happened to the first one", () => {
    for (const status of ["claimed", "requested", "proof_submitted", "cancelled", "expired"] as const) {
      const result = claimAvailability({ campaign: campaign(), now: NOW, inAudience: true, claim: { status } });
      expect(result).toMatchObject({ state: "already_claimed", canClaim: false });
    }
    const dropped = claimAvailability({ campaign: campaign(), now: NOW, inAudience: true, claim: { status: "cancelled" } });
    expect(dropped.detail).toMatch(/once/);
  });

  it("checks the creator's own claim before the campaign's state", () => {
    const result = claimAvailability({
      campaign: campaign({ status: "full", slotsTaken: 20 }),
      now: NOW,
      inAudience: true,
      claim: { status: "claimed" },
    });
    expect(result.state).toBe("already_claimed");
    expect(result.title).toBe("You're in");
  });
});

describe("canDropClaim", () => {
  it("allows dropping until the post window starts", () => {
    expect(canDropClaim("claimed", timing, NOW)).toBe(true);
    expect(canDropClaim("claimed", timing, at("2026-11-03T15:59:59Z"))).toBe(true);
    expect(canDropClaim("claimed", timing, at("2026-11-03T16:00:00Z"))).toBe(false);
    expect(canDropClaim("draft_approved", timing, at("2026-11-03T18:00:00Z"))).toBe(false);
  });

  it("covers requests and every draft state, but not proof or later", () => {
    for (const status of ["requested", "draft_submitted", "changes_requested", "draft_approved"] as const) {
      expect(canDropClaim(status, timing, NOW)).toBe(true);
    }
    for (const status of ["proof_submitted", "approved", "rejected", "paid", "expired", "cancelled"] as const) {
      expect(canDropClaim(status, timing, NOW)).toBe(false);
    }
  });
});

describe("applyDeadlines", () => {
  const base: CreatorClaim = { campaignId: "c", status: "claimed", payout: { amount: "1", currency: "USD" }, events: [] };

  it("expires a claim with no proof at the proof deadline, and only then", () => {
    expect(applyDeadlines(base, timing, at("2026-11-04T11:59:59Z")).status).toBe("claimed");
    const expired = applyDeadlines(base, timing, at("2026-11-04T12:00:00Z"));
    expect(expired.status).toBe("expired");
    expect(expired.events.at(-1)).toMatchObject({ status: "expired", at: timing.proofDeadline });
    expect(applyDeadlines({ ...base, status: "rejected" }, timing, at("2026-11-05T00:00:00Z")).status).toBe("expired");
  });

  it("never expires proof that is already in, or a settled claim", () => {
    for (const status of ["proof_submitted", "approved", "paid", "cancelled"] as const) {
      expect(applyDeadlines({ ...base, status }, timing, at("2026-12-01T00:00:00Z")).status).toBe(status);
    }
  });

  it("declines a request still waiting when claiming closes", () => {
    const request = { ...base, status: "requested" as const };
    expect(applyDeadlines(request, timing, at("2026-11-03T13:59:00Z")).status).toBe("requested");
    expect(applyDeadlines(request, timing, at("2026-11-03T14:00:00Z")).status).toBe("cancelled");
  });
});

describe("canMoveClaim", () => {
  it("sends drafts only when the campaign needs one", () => {
    expect(canMoveClaim("claimed", "draft_submitted", { draftRequired: true })).toBe(true);
    expect(canMoveClaim("claimed", "draft_submitted", { draftRequired: false })).toBe(false);
    expect(canMoveClaim("claimed", "proof_submitted", { draftRequired: false })).toBe(true);
    expect(canMoveClaim("claimed", "proof_submitted", { draftRequired: true })).toBe(false);
  });

  it("follows the loop and stops at the end", () => {
    const opts = { draftRequired: true };
    expect(canMoveClaim("changes_requested", "draft_submitted", opts)).toBe(true);
    expect(canMoveClaim("rejected", "proof_submitted", opts)).toBe(true);
    expect(canMoveClaim("approved", "paid", opts)).toBe(true);
    expect(canMoveClaim("paid", "approved", opts)).toBe(false);
    expect(canMoveClaim("requested", "proof_submitted", opts)).toBe(false);
    expect(canMoveClaim("proof_submitted", "cancelled", opts)).toBe(false);
  });
});

describe("claimPath", () => {
  it("adds a request step for apply mode and draft steps when a draft is required", () => {
    expect(claimPath({ claimMode: "instant", draftRequired: false })).toEqual(["claimed", "proof_submitted", "approved", "paid"]);
    expect(claimPath({ claimMode: "apply", draftRequired: true })).toEqual([
      "requested",
      "claimed",
      "draft_submitted",
      "draft_approved",
      "proof_submitted",
      "approved",
      "paid",
    ]);
  });

  it("places loop-backs on the step they repeat, and stopped claims off the path", () => {
    const path = claimPath({ claimMode: "instant", draftRequired: true });
    expect(pathPosition(path, "claimed")).toBe(0);
    expect(pathPosition(path, "changes_requested")).toBe(1);
    expect(pathPosition(path, "rejected")).toBe(3);
    expect(pathPosition(path, "paid")).toBe(5);
    expect(pathPosition(path, "cancelled")).toBe(-1);
    expect(pathPosition(path, "expired")).toBe(-1);
  });
});

describe("nextStep", () => {
  it("asks for a draft first when the campaign needs one", () => {
    expect(nextStep("claimed", { draftRequired: true })).toMatchObject({ title: "Write your draft", actor: "you" });
    expect(nextStep("claimed", { draftRequired: false })).toMatchObject({ title: "Post inside your window", actor: "you" });
  });

  it("says who moves next", () => {
    expect(nextStep("requested", { draftRequired: false }).actor).toBe("agency");
    expect(nextStep("changes_requested", { draftRequired: true }).actor).toBe("you");
    expect(nextStep("proof_submitted", { draftRequired: false }).actor).toBe("agency");
    expect(nextStep("paid", { draftRequired: false }).actor).toBeNull();
  });

  it("has plain copy for every status, with no dashes", () => {
    for (const status of CLAIM_STATUSES) {
      for (const draftRequired of [true, false]) {
        const step = nextStep(status, { draftRequired });
        expect(step.title.length).toBeGreaterThan(0);
        expect(`${step.title} ${step.detail}`).not.toMatch(/[–—]/);
      }
    }
  });
});

describe("claimClock", () => {
  it("counts down to the window, then its end, then the proof deadline", () => {
    expect(claimClock("claimed", timing, NOW)).toEqual({ label: "Window opens in", to: timing.postWindowStart });
    expect(claimClock("claimed", timing, at("2026-11-03T17:00:00Z"))).toEqual({
      label: "Window closes in",
      to: timing.postWindowEnd,
    });
    expect(claimClock("draft_approved", timing, at("2026-11-03T21:00:00Z"))).toEqual({
      label: "Proof due in",
      to: timing.proofDeadline,
    });
    expect(claimClock("claimed", timing, at("2026-11-05T00:00:00Z"))).toBeNull();
  });

  it("stops ticking once proof is in", () => {
    expect(claimClock("proof_submitted", timing, NOW)).toBeNull();
    expect(claimClock("paid", timing, NOW)).toBeNull();
    expect(claimClock("rejected", timing, NOW)).toEqual({ label: "Proof due in", to: timing.proofDeadline });
  });
});

describe("attentionFor", () => {
  const noDraft = { draftRequired: false };
  it("flags changes and rejections straight away", () => {
    expect(attentionFor("changes_requested", timing, NOW, { draftRequired: true })).toBe("changes_requested");
    expect(attentionFor("rejected", timing, NOW, noDraft)).toBe("rejected");
  });

  it("flags proof once the window is open, and a window about to open", () => {
    expect(attentionFor("claimed", timing, NOW, noDraft)).toBeNull();
    expect(attentionFor("claimed", timing, at("2026-11-03T08:00:00Z"), noDraft)).toBe("window_soon");
    expect(attentionFor("claimed", timing, at("2026-11-03T18:00:00Z"), noDraft)).toBe("proof_due");
    expect(attentionFor("proof_submitted", timing, at("2026-11-03T18:00:00Z"), noDraft)).toBeNull();
  });

  it("flags a missing draft two days before the window", () => {
    expect(attentionFor("claimed", timing, at("2026-10-28T09:00:00Z"), { draftRequired: true })).toBeNull();
    expect(attentionFor("claimed", timing, NOW, { draftRequired: true })).toBeNull();
    expect(attentionFor("claimed", timing, at("2026-11-02T09:00:00Z"), { draftRequired: true })).toBe("draft_due");
  });
});

describe("myCampaignTab", () => {
  it("sorts every status into one tab", () => {
    expect(myCampaignTab("claimed")).toBe("active");
    expect(myCampaignTab("changes_requested")).toBe("active");
    expect(myCampaignTab("draft_approved")).toBe("active");
    expect(myCampaignTab("rejected")).toBe("active");
    expect(myCampaignTab("requested")).toBe("submitted");
    expect(myCampaignTab("draft_submitted")).toBe("submitted");
    expect(myCampaignTab("proof_submitted")).toBe("submitted");
    expect(myCampaignTab("approved")).toBe("approved");
    expect(myCampaignTab("paid")).toBe("paid");
    expect(myCampaignTab("expired")).toBe("past");
    expect(myCampaignTab("cancelled")).toBe("past");
  });
});

describe("earnings", () => {
  const claim = (campaignId: string, status: CreatorClaim["status"], amount: string, currency: string): CreatorClaim => ({
    campaignId,
    status,
    payout: { amount, currency },
    events: [],
  });

  it("creates an earning for approved and paid claims only", () => {
    const rows = earningsFromClaims([
      claim("a", "approved", "250", "USDC"),
      claim("b", "paid", "400", "USD"),
      claim("c", "claimed", "150", "USD"),
      claim("d", "expired", "60", "USDT"),
    ]);
    expect(rows.map((row) => [row.campaignId, row.status])).toEqual([
      ["a", "unpaid"],
      ["b", "paid"],
    ]);
  });

  it("keeps totals per currency and never adds USD to NGN", () => {
    const summary = earningsSummary(
      earningsFromClaims([
        claim("a", "paid", "200", "USD"),
        claim("b", "paid", "150.50", "USD"),
        claim("c", "approved", "95000", "NGN"),
        claim("d", "approved", "120", "USDC"),
      ]),
    );
    expect(summary.paid).toEqual([{ currency: "USD", amount: "350.50" }]);
    expect(summary.unpaid).toEqual([
      { currency: "NGN", amount: "95000.00" },
      { currency: "USDC", amount: "120.00" },
    ]);
    expect(summary.total).toHaveLength(3);
  });
});

describe("parseXPostUrl", () => {
  const post = { handle: "amarabuilds", postId: "1975000000000000101" };

  it("reads x.com and twitter.com links", () => {
    expect(parseXPostUrl("https://x.com/amarabuilds/status/1975000000000000101")).toEqual(post);
    expect(parseXPostUrl("https://twitter.com/amarabuilds/status/1975000000000000101")).toEqual(post);
    expect(parseXPostUrl("https://www.twitter.com/amarabuilds/status/1975000000000000101")).toEqual(post);
  });

  it("reads mobile links and links pasted without https", () => {
    expect(parseXPostUrl("https://mobile.twitter.com/amarabuilds/status/1975000000000000101")).toEqual(post);
    expect(parseXPostUrl("mobile.twitter.com/amarabuilds/status/1975000000000000101")).toEqual(post);
    expect(parseXPostUrl("  x.com/amarabuilds/status/1975000000000000101  ")).toEqual(post);
  });

  it("ignores tracking query strings, fragments and media segments", () => {
    expect(parseXPostUrl("https://x.com/amarabuilds/status/1975000000000000101?s=20&t=abc123")).toEqual(post);
    expect(parseXPostUrl("https://twitter.com/amarabuilds/status/1975000000000000101?ref_src=twsrc%5Etfw#m")).toEqual(post);
    expect(parseXPostUrl("https://x.com/amarabuilds/status/1975000000000000101/photo/1")).toEqual(post);
  });

  it("returns null for anything that isn't a post link", () => {
    expect(parseXPostUrl("")).toBeNull();
    expect(parseXPostUrl("not a link")).toBeNull();
    expect(parseXPostUrl("https://x.com/amarabuilds")).toBeNull();
    expect(parseXPostUrl("https://x.com/amarabuilds/likes")).toBeNull();
    expect(parseXPostUrl("https://x.com/amarabuilds/status/abc")).toBeNull();
    expect(parseXPostUrl("https://x.com/i/web/status/1975000000000000101")).toBeNull();
    expect(parseXPostUrl("https://x.com/i/status/1975000000000000101")).toBeNull();
    expect(parseXPostUrl("https://x.com.evil.example/amarabuilds/status/1")).toBeNull();
    expect(parseXPostUrl("https://x.com@evil.example/amarabuilds/status/1")).toBeNull();
    expect(parseXPostUrl("https://instagram.com/p/abc")).toBeNull();
    expect(parseXPostUrl("ftp://x.com/amarabuilds/status/1")).toBeNull();
  });
});

describe("normalizeXPostUrl", () => {
  it("gives every form of the same post one link, without tracking", () => {
    const canonical = "https://x.com/amarabuilds/status/1975000000000000101";
    expect(normalizeXPostUrl("https://twitter.com/amarabuilds/status/1975000000000000101?s=20")).toBe(canonical);
    expect(normalizeXPostUrl("mobile.twitter.com/amarabuilds/status/1975000000000000101/photo/1")).toBe(canonical);
    expect(normalizeXPostUrl("x.com/amarabuilds/status/1975000000000000101")).toBe(canonical);
    expect(normalizeXPostUrl("https://x.com/amarabuilds")).toBeNull();
  });
});

describe("checkProofLink", () => {
  const me = { platform: "x" as const, handle: "@amarabuilds" };

  it("passes the creator's own post and saves it without tracking", () => {
    const result = checkProofLink("https://twitter.com/AmaraBuilds/status/42?s=20", me);
    expect(result.ok).toBe(true);
    expect(result.normalized).toBe("https://x.com/AmaraBuilds/status/42");
    expect(result.checks.every((check) => check.ok)).toBe(true);
  });

  it("fails a post from someone else and names both handles", () => {
    const result = checkProofLink("https://x.com/theoships/status/42", me);
    expect(result.ok).toBe(false);
    expect(result.checks.find((check) => check.id === "handle")?.label).toBe(
      "This post is from @theoships, not @amarabuilds",
    );
  });

  it("fails text that isn't a post link", () => {
    const result = checkProofLink("hello", me);
    expect(result.ok).toBe(false);
    expect(result.normalized).toBeNull();
  });

  it("checks the host for other platforms", () => {
    expect(checkProofLink("https://www.instagram.com/reel/Cx1abc/?igsh=xyz", { platform: "instagram", handle: "@a" }).ok).toBe(
      true,
    );
    expect(checkProofLink("https://x.com/a/status/1", { platform: "instagram", handle: "@a" }).ok).toBe(false);
  });

  it("matches handles without the @ and regardless of case", () => {
    expect(sameHandle("@AmaraBuilds", "amarabuilds")).toBe(true);
    expect(sameHandle("@", "")).toBe(false);
  });
});

describe("proof and request forms", () => {
  it("takes a request note of 10 to 500 characters", () => {
    expect(requestNoteSchema.safeParse({ note: "Too short" }).success).toBe(false);
    expect(requestNoteSchema.safeParse({ note: "Ten chars!" }).success).toBe(true);
    expect(requestNoteSchema.safeParse({ note: "a".repeat(500) }).success).toBe(true);
    expect(requestNoteSchema.safeParse({ note: "a".repeat(501) }).success).toBe(false);
    expect(requestNoteSchema.safeParse({ note: "   padded      " }).success).toBe(false);
  });

  it("needs a valid own post and both confirmations", () => {
    const schema = makeProofSchema({ platform: "x", handle: "@amarabuilds" });
    const valid = { url: "x.com/amarabuilds/status/42", labelUsed: true, briefFollowed: true };
    expect(schema.safeParse(valid).success).toBe(true);
    expect(schema.safeParse({ ...valid, labelUsed: false }).success).toBe(false);
    expect(schema.safeParse({ ...valid, briefFollowed: false }).success).toBe(false);
    const other = schema.safeParse({ ...valid, url: "x.com/theoships/status/42" });
    expect(other.success).toBe(false);
    expect(other.error?.issues[0]?.message).toMatch(/theoships/);
  });

  it("spots required tags in a draft", () => {
    expect(tagsFound("Built it with #Nebula2 and @Nebula_AI", ["@nebula_ai", "#Nebula2", "agent builder"])).toEqual({
      "@nebula_ai": true,
      "#Nebula2": true,
      "agent builder": false,
    });
  });
});

describe("dateBucket", () => {
  it("sorts windows into today, this week and later in the viewer's zone", () => {
    expect(dateBucket("2026-11-01T22:00:00Z", NOW, "UTC")).toBe("today");
    expect(dateBucket("2026-11-02T01:00:00Z", NOW, "UTC")).toBe("week");
    expect(dateBucket("2026-11-08T12:00:00Z", NOW, "UTC")).toBe("week");
    expect(dateBucket("2026-11-09T12:00:00Z", NOW, "UTC")).toBe("later");
  });

  it("counts a window that already started as today", () => {
    expect(dateBucket("2026-10-30T12:00:00Z", NOW, "UTC")).toBe("today");
  });

  it("uses the calendar day where the viewer is", () => {
    // In Auckland it's 22:00 on 1 Nov, and the window starts at 11:00 on 2 Nov: tomorrow there.
    expect(dateBucket("2026-11-01T22:00:00Z", NOW, "Pacific/Auckland")).toBe("week");
  });
});

describe("isNewDrop", () => {
  it("marks drops from the last three days as new", () => {
    expect(isNewDrop("2026-10-31T12:00:00Z", NOW)).toBe(true);
    expect(isNewDrop("2026-10-29T09:00:01Z", NOW)).toBe(true);
    expect(isNewDrop("2026-10-29T09:00:00Z", NOW)).toBe(false);
  });
});

describe("sortCampaigns", () => {
  const item = (id: string, droppedAt: string, amount: string, currency: string, claimDeadline: string) => ({
    id,
    droppedAt,
    payout: { amount, currency },
    timing: { claimDeadline },
  });
  const list = [
    item("a", "2026-10-30T15:00:00Z", "320", "USDC", "2026-11-03T14:00:00Z"),
    item("b", "2026-10-31T12:00:00Z", "400", "USD", "2026-11-04T18:00:00Z"),
    item("c", "2026-11-01T08:00:00Z", "180000", "NGN", "2026-11-02T11:00:00Z"),
    item("d", "2026-10-29T10:00:00Z", "150", "USD", "2026-10-31T10:00:00Z"),
  ];

  it("puts the newest drop first", () => {
    expect(sortCampaigns(list, "newest", NOW).map((row) => row.id)).toEqual(["c", "b", "a", "d"]);
  });

  it("puts the soonest open deadline first and closed ones last", () => {
    expect(sortCampaigns(list, "ending", NOW).map((row) => row.id)).toEqual(["c", "a", "b", "d"]);
  });

  it("ranks payouts within comparable currencies, never converting NGN", () => {
    expect(sortCampaigns(list, "payout", NOW).map((row) => row.id)).toEqual(["b", "a", "d", "c"]);
  });
});

describe("calendar files", () => {
  it("writes UTC timestamps in the compact form", () => {
    expect(icsTimestamp("2026-11-03T16:00:00Z")).toBe("20261103T160000Z");
    expect(icsTimestamp("2026-11-03T17:30:00+01:00")).toBe("20261103T163000Z");
  });

  it("escapes commas, semicolons, backslashes and new lines", () => {
    expect(escapeIcsText("Post, then; prove\\it\nnow")).toBe("Post\\, then\\; prove\\\\it\\nnow");
  });

  it("folds long lines at 75 bytes without splitting characters", () => {
    const folded = foldIcsLine(`DESCRIPTION:${"é".repeat(80)}`);
    const lines = folded.split("\r\n");
    expect(lines.length).toBeGreaterThan(1);
    for (const line of lines) expect(new TextEncoder().encode(line).length).toBeLessThanOrEqual(75);
    expect(lines.slice(1).every((line) => line.startsWith(" "))).toBe(true);
    expect(folded.replace(/\r\n /g, "")).toBe(`DESCRIPTION:${"é".repeat(80)}`);
  });

  it("builds a valid calendar with a reminder", () => {
    const ics = buildIcs(
      [
        {
          uid: "cmp-nebula-2-window@agi2027",
          title: "Post for Nebula AI, Nebula 2.0 launch day",
          start: timing.postWindowStart,
          end: timing.postWindowEnd,
          description: "Your angle: The 10-minute build",
          url: "https://agi2027.example/dashboard/campaigns/cmp-nebula-2",
          alarmMinutesBefore: 30,
        },
      ],
      NOW,
    );
    expect(ics.startsWith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n")).toBe(true);
    expect(ics.endsWith("END:VCALENDAR\r\n")).toBe(true);
    expect(ics).not.toMatch(/[^\r]\n/);
    expect(ics).toContain("DTSTAMP:20261101T090000Z");
    expect(ics).toContain("DTSTART:20261103T160000Z");
    expect(ics).toContain("DTEND:20261103T200000Z");
    expect(ics).toContain("SUMMARY:Post for Nebula AI\\, Nebula 2.0 launch day");
    expect(ics).toContain("TRIGGER:-PT30M");
    expect(ics.match(/BEGIN:VEVENT/g)).toHaveLength(1);
  });
});
