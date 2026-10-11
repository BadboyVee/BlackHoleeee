import { describe, expect, it } from "vitest";

import { campaignToFormInput, hasDropped } from "@/components/admin/campaign-builder/form-values";
import { demoCampaigns, demoRosters } from "@/lib/campaigns/demo";
import {
  amountSchema,
  campaignCommitment,
  campaignWarnings,
  handleSchema,
  hashtagSchema,
  linkSchema,
  makeCampaignSchema,
  type CampaignFormInput,
  type CampaignFormValues,
} from "@/lib/campaigns/schema";

const NOW = new Date("2026-10-15T00:00:00Z");
const schema = makeCampaignSchema(() => NOW);

/** A complete campaign that passes every rule, scheduled to drop on 20 Oct. */
function validCampaign(): CampaignFormInput {
  return {
    clientId: "c-nebula",
    newClient: undefined,
    title: "Nebula 2.0 launch day",
    summary: "Quote the launch post with your honest first take on the agent builder.",
    brief: {
      about: "Nebula builds AI agents that run inside a company's own tools.",
      whatToSay: "Try the builder for ten minutes, then quote the launch post with what surprised you.",
      keyMessage: "Anyone on your team can build a working agent in an afternoon.",
      dos: ["Use the paid partnership label"],
      donts: ["Don't promise returns or results"],
    },
    angles: ["The 10-minute build", "Why this matters for non-engineers"],
    deliverable: "quote",
    platform: "x",
    links: {
      targetPostUrl: "https://x.com/nebula_ai/status/1975000000000000001",
      trackingUrl: "https://nebula.example/?ref=agi2027",
    },
    requiredTags: { mentions: ["@nebula_ai"], hashtags: ["#Nebula2"], keywords: ["agent builder"] },
    assets: { brandKitUrl: "https://nebula.example/brand", files: [{ name: "hero.png", kind: "image", sizeBytes: 1_840_000 }] },
    payout: { amount: "250", currency: "USDC" },
    tierPayouts: [{ tier: "Tier 1", amount: "320" }],
    creatorPayouts: [],
    slots: 20,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: {
      dropAt: "2026-10-20T09:00:00Z",
      postWindowStart: "2026-11-03T16:00:00Z",
      postWindowEnd: "2026-11-03T20:00:00Z",
      claimDeadline: "2026-11-03T14:00:00Z",
      proofDeadline: "2026-11-04T12:00:00Z",
    },
    publish: "schedule",
    internal: { notes: "Client wants every post inside four hours.", budgetAmount: "7000", budgetCurrency: "USDC" },
  };
}

/** The valid campaign with some fields replaced. */
function campaign(patch: (value: CampaignFormInput) => void): CampaignFormInput {
  const value = validCampaign();
  patch(value);
  return value;
}

/** The distinct paths that failed, e.g. ["timing.dropAt"]. */
function failedPaths(input: CampaignFormInput, parser = schema) {
  const result = parser.safeParse(input);
  if (result.success) return [];
  return [...new Set(result.error.issues.map((issue) => issue.path.join(".")))];
}

function messagesAt(input: CampaignFormInput, path: string) {
  const result = schema.safeParse(input);
  if (result.success) return [];
  return result.error.issues.filter((issue) => issue.path.join(".") === path).map((issue) => issue.message);
}

function parsed(input: CampaignFormInput): CampaignFormValues {
  return schema.parse(input);
}

describe("campaignSchema", () => {
  it("accepts a complete campaign", () => {
    expect(failedPaths(validCampaign())).toEqual([]);
  });

  it("asks for the brand's name when adding a new brand", () => {
    expect(failedPaths(campaign((v) => (v.clientId = "new")))).toEqual(["newClient.name"]);
    expect(
      failedPaths(
        campaign((v) => {
          v.clientId = "new";
          v.newClient = { name: "", website: "", xHandle: "" };
        }),
      ),
    ).toEqual(["newClient.name"]);
  });

  it("accepts a new brand with a name, and normalises its handle", () => {
    const value = parsed(
      campaign((v) => {
        v.clientId = "new";
        v.newClient = { name: "Parallax", website: "https://parallax.example", xHandle: "parallax_hq" };
      }),
    );
    expect(value.newClient).toEqual({ name: "Parallax", website: "https://parallax.example", xHandle: "@parallax_hq" });
  });

  it("needs a brand to be picked", () => {
    expect(failedPaths(campaign((v) => (v.clientId = "")))).toEqual(["clientId"]);
  });

  it("needs the post to quote or reply to", () => {
    expect(failedPaths(campaign((v) => (v.links.targetPostUrl = "")))).toEqual(["links.targetPostUrl"]);
    expect(
      failedPaths(
        campaign((v) => {
          v.deliverable = "reply";
          v.links.targetPostUrl = "";
        }),
      ),
    ).toEqual(["links.targetPostUrl"]);
  });

  it("doesn't need a target post for an original post", () => {
    expect(
      failedPaths(
        campaign((v) => {
          v.deliverable = "original";
          v.links.targetPostUrl = "";
        }),
      ),
    ).toEqual([]);
  });

  it("needs at least one pick for a narrowed audience", () => {
    expect(failedPaths(campaign((v) => (v.audience.kind = "tiers")))).toEqual(["audience.tiers"]);
    expect(failedPaths(campaign((v) => (v.audience.kind = "tags")))).toEqual(["audience.tags"]);
    expect(failedPaths(campaign((v) => (v.audience.kind = "creators")))).toEqual(["audience.creatorIds"]);
    expect(
      failedPaths(
        campaign((v) => {
          v.audience = { kind: "creators", tiers: [], tags: [], creatorIds: ["u-theo"] };
          v.slots = 1;
        }),
      ),
    ).toEqual([]);
  });

  it("allows one custom amount per tier", () => {
    expect(
      failedPaths(
        campaign((v) => {
          v.tierPayouts = [
            { tier: "Tier 1", amount: "320" },
            { tier: "Tier 1", amount: "300" },
          ];
        }),
      ),
    ).toEqual(["tierPayouts"]);
  });

  it("needs the post window to end after it starts", () => {
    expect(failedPaths(campaign((v) => (v.timing.postWindowEnd = "2026-11-03T15:00:00Z")))).toEqual([
      "timing.postWindowEnd",
    ]);
    expect(failedPaths(campaign((v) => (v.timing.postWindowEnd = v.timing.postWindowStart)))).toEqual([
      "timing.postWindowEnd",
    ]);
  });

  it("closes claiming before the window ends", () => {
    expect(failedPaths(campaign((v) => (v.timing.claimDeadline = "2026-11-03T21:00:00Z")))).toEqual([
      "timing.claimDeadline",
    ]);
  });

  it("keeps the proof deadline at or after the window end", () => {
    expect(failedPaths(campaign((v) => (v.timing.proofDeadline = "2026-11-03T19:00:00Z")))).toEqual([
      "timing.proofDeadline",
    ]);
    expect(failedPaths(campaign((v) => (v.timing.proofDeadline = v.timing.postWindowEnd)))).toEqual([]);
  });

  it("needs a drop time when scheduling", () => {
    const input = campaign((v) => (v.timing.dropAt = ""));
    expect(failedPaths(input)).toEqual(["timing.dropAt"]);
    expect(messagesAt(input, "timing.dropAt")).toEqual(["Pick when the campaign drops"]);
  });

  it("needs the drop time to be in the future", () => {
    const input = campaign((v) => (v.timing.dropAt = "2026-10-14T09:00:00Z"));
    expect(failedPaths(input)).toEqual(["timing.dropAt"]);
    expect(messagesAt(input, "timing.dropAt")).toEqual(["The drop time has to be in the future"]);
  });

  it("drops the campaign before claiming closes", () => {
    const input = campaign((v) => (v.timing.dropAt = "2026-11-03T15:00:00Z"));
    expect(failedPaths(input)).toEqual(["timing.dropAt"]);
    expect(messagesAt(input, "timing.dropAt")).toEqual(["Drop it before claiming closes"]);
  });

  it("ignores the drop time unless scheduling", () => {
    expect(
      failedPaths(
        campaign((v) => {
          v.publish = "now";
          v.timing.dropAt = "";
        }),
      ),
    ).toEqual([]);
  });

  it("won't publish a campaign whose claiming has already closed, but keeps it as a draft", () => {
    const past = (v: CampaignFormInput) => {
      v.timing = {
        dropAt: "",
        postWindowStart: "2026-10-10T16:00:00Z",
        postWindowEnd: "2026-10-10T20:00:00Z",
        claimDeadline: "2026-10-10T14:00:00Z",
        proofDeadline: "2026-10-11T12:00:00Z",
      };
    };
    expect(failedPaths(campaign((v) => (past(v), (v.publish = "now"))))).toEqual(["timing.claimDeadline"]);
    expect(failedPaths(campaign((v) => (past(v), (v.publish = "draft"))))).toEqual([]);
  });

  it("skips the publish checks for a campaign that has already dropped", () => {
    const dropped = makeCampaignSchema(() => NOW, { alreadyDropped: true });
    const input = campaign((v) => {
      v.publish = "now";
      v.timing = {
        dropAt: "",
        postWindowStart: "2026-10-06T14:00:00Z",
        postWindowEnd: "2026-10-07T14:00:00Z",
        claimDeadline: "2026-10-06T10:00:00Z",
        proofDeadline: "2026-10-08T12:00:00Z",
      };
    });
    expect(failedPaths(input, dropped)).toEqual([]);
    // The order of the times still matters.
    expect(failedPaths({ ...input, timing: { ...input.timing, proofDeadline: "2026-10-07T13:00:00Z" } }, dropped)).toEqual([
      "timing.proofDeadline",
    ]);
  });

  it("needs real times", () => {
    expect(failedPaths(campaign((v) => (v.timing.postWindowStart = "")))).toEqual(["timing.postWindowStart"]);
    expect(failedPaths(campaign((v) => (v.timing.postWindowStart = "2026-11-03T16:00")))).toEqual([
      "timing.postWindowStart",
    ]);
  });

  it("normalises mentions and hashtags in the campaign", () => {
    const value = parsed(
      campaign((v) => {
        v.requiredTags = { mentions: ["nebula_ai", " @nebula_ai2 "], hashtags: ["Nebula2", "#AgentBuilder"], keywords: [] };
      }),
    );
    expect(value.requiredTags.mentions).toEqual(["@nebula_ai", "@nebula_ai2"]);
    expect(value.requiredTags.hashtags).toEqual(["#Nebula2", "#AgentBuilder"]);
  });

  it("rejects links creators shouldn't open", () => {
    expect(failedPaths(campaign((v) => (v.links.trackingUrl = "javascript:alert(1)")))).toEqual(["links.trackingUrl"]);
    expect(failedPaths(campaign((v) => (v.links.trackingUrl = "nebula.example")))).toEqual(["links.trackingUrl"]);
    expect(failedPaths(campaign((v) => (v.assets.brandKitUrl = "mailto:brand@nebula.example")))).toEqual([
      "assets.brandKitUrl",
    ]);
  });

  it("keeps the summary to one line", () => {
    expect(failedPaths(campaign((v) => (v.summary = "x".repeat(141))))).toEqual(["summary"]);
    expect(failedPaths(campaign((v) => (v.summary = "x".repeat(140))))).toEqual([]);
  });

  it("checks each payout amount", () => {
    expect(failedPaths(campaign((v) => (v.payout.amount = "250.555")))).toEqual(["payout.amount"]);
    expect(failedPaths(campaign((v) => (v.tierPayouts = [{ tier: "Tier 2", amount: "0" }])))).toEqual([
      "tierPayouts.0.amount",
    ]);
    expect(failedPaths(campaign((v) => (v.internal.budgetAmount = "6,000")))).toEqual(["internal.budgetAmount"]);
  });

  it("needs at least one slot, in whole numbers", () => {
    expect(failedPaths(campaign((v) => (v.slots = 0)))).toEqual(["slots"]);
    expect(failedPaths(campaign((v) => (v.slots = 2.5)))).toEqual(["slots"]);
    expect(failedPaths(campaign((v) => (v.slots = 1001)))).toEqual(["slots"]);
  });
});

describe("handleSchema and hashtagSchema", () => {
  it("adds the @ to a handle and trims it", () => {
    expect(handleSchema.parse("nebula_ai")).toBe("@nebula_ai");
    expect(handleSchema.parse("@nebula_ai")).toBe("@nebula_ai");
    expect(handleSchema.parse("  orbitar ")).toBe("@orbitar");
  });

  it("rejects handles X wouldn't allow", () => {
    expect(handleSchema.safeParse("nebula ai").success).toBe(false);
    expect(handleSchema.safeParse("a_handle_that_is_too_long").success).toBe(false);
    expect(handleSchema.safeParse("@@nebula").success).toBe(false);
    expect(handleSchema.safeParse("").success).toBe(false);
  });

  it("adds the # to a hashtag and allows letters in any language", () => {
    expect(hashtagSchema.parse("Nebula2")).toBe("#Nebula2");
    expect(hashtagSchema.parse("#Nebula2")).toBe("#Nebula2");
    expect(hashtagSchema.parse("Lagos2026")).toBe("#Lagos2026");
    expect(hashtagSchema.parse("café")).toBe("#café");
  });

  it("rejects hashtags with spaces or punctuation", () => {
    expect(hashtagSchema.safeParse("two words").success).toBe(false);
    expect(hashtagSchema.safeParse("launch-day").success).toBe(false);
    expect(hashtagSchema.safeParse("#").success).toBe(false);
  });
});

describe("amountSchema", () => {
  it("accepts whole numbers and up to two decimals", () => {
    for (const amount of ["250", "99.50", "0.5", "180000", "180000.00", " 250 "]) {
      expect(amountSchema.safeParse(amount).success, amount).toBe(true);
    }
    expect(amountSchema.parse(" 250 ")).toBe("250");
  });

  it("rejects anything that isn't an exact positive amount", () => {
    for (const amount of ["", "0", "0.00", "-5", "1,000", "1.234", "250 USDC", "$250", "1e3", "abc"]) {
      expect(amountSchema.safeParse(amount).success, amount).toBe(false);
    }
  });

  it("explains what went wrong", () => {
    expect(amountSchema.safeParse("1,000").error?.issues[0]?.message).toBe("Use a number like 250 or 99.50");
    expect(amountSchema.safeParse("0").error?.issues[0]?.message).toBe("Must be more than 0");
  });
});

describe("linkSchema", () => {
  it("accepts http and https links on a real domain", () => {
    expect(linkSchema.safeParse("https://x.com/nebula_ai/status/1").success).toBe(true);
    expect(linkSchema.safeParse("http://nebula.example/brand").success).toBe(true);
  });

  it("rejects other protocols and bare words", () => {
    for (const link of ["javascript:alert(1)", "mailto:hi@nebula.example", "ftp://nebula.example", "https://localhost"]) {
      expect(linkSchema.safeParse(link).success, link).toBe(false);
    }
  });
});

describe("campaignCommitment", () => {
  it("multiplies exactly, without floating point drift", () => {
    expect(
      campaignCommitment({ payout: { amount: "0.10", currency: "USDC" }, slots: 3, tierPayouts: [], creatorPayouts: [] }),
    ).toEqual({ currency: "USDC", base: "0.30", low: "0.30", high: "0.30", varies: false });
  });

  it("shows the range custom amounts create", () => {
    expect(
      campaignCommitment({
        payout: { amount: "250", currency: "USDC" },
        slots: 20,
        tierPayouts: [{ amount: "320" }, { amount: "200" }],
        creatorPayouts: [],
      }),
    ).toEqual({ currency: "USDC", base: "5000.00", low: "4000.00", high: "6400.00", varies: true });
  });

  it("waits for a valid amount and slot count", () => {
    const rest = { tierPayouts: [], creatorPayouts: [] };
    expect(campaignCommitment({ payout: { amount: "", currency: "USD" }, slots: 10, ...rest })).toBeNull();
    expect(campaignCommitment({ payout: { amount: "12,5", currency: "USD" }, slots: 10, ...rest })).toBeNull();
    expect(campaignCommitment({ payout: { amount: "100", currency: "USD" }, slots: Number.NaN, ...rest })).toBeNull();
  });

  it("ignores custom amounts that aren't valid yet", () => {
    expect(
      campaignCommitment({
        payout: { amount: "100", currency: "USD" },
        slots: 2,
        tierPayouts: [{ amount: "" }],
        creatorPayouts: [{ amount: "abc" }],
      }),
    ).toEqual({ currency: "USD", base: "200.00", low: "200.00", high: "200.00", varies: false });
  });
});

describe("campaignWarnings", () => {
  it("has nothing to say about a well set up campaign", () => {
    expect(campaignWarnings(parsed(validCampaign()))).toEqual([]);
  });

  it("flags a payout above the budget", () => {
    const value = parsed(campaign((v) => (v.internal.budgetAmount = "4000")));
    expect(campaignWarnings(value)).toEqual([
      "Paying every slot costs 5,000 USDC, more than the 4,000 USDC budget.",
    ]);
  });

  it("flags when the highest custom amount would break the budget", () => {
    const value = parsed(campaign((v) => (v.internal.budgetAmount = "6000")));
    expect(campaignWarnings(value)).toEqual([
      "If every slot is paid the highest custom amount, it costs 6,400 USDC, more than the 6,000 USDC budget.",
    ]);
  });

  it("formats fiat budgets with their symbol", () => {
    const value = parsed(
      campaign((v) => {
        v.payout = { amount: "180000", currency: "NGN" };
        v.tierPayouts = [];
        v.slots = 12;
        v.internal = { notes: "", budgetAmount: "2000000", budgetCurrency: "NGN" };
      }),
    );
    expect(campaignWarnings(value)).toEqual(["Paying every slot costs ₦2,160,000, more than the ₦2,000,000 budget."]);
  });

  it("never compares a budget in another currency", () => {
    const value = parsed(campaign((v) => (v.internal.budgetCurrency = "USD")));
    expect(campaignWarnings(value)).toEqual([
      "The budget is in USD and payouts are in USDC, so they can't be compared.",
    ]);
  });

  it("has no budget check without a budget", () => {
    expect(campaignWarnings(parsed(campaign((v) => (v.internal.budgetAmount = ""))))).toEqual([]);
  });

  it("flags more slots than hand-picked creators", () => {
    const value = parsed(
      campaign((v) => {
        v.audience = { kind: "creators", tiers: [], tags: [], creatorIds: ["u-theo", "u-lucia"] };
        v.slots = 4;
      }),
    );
    expect(campaignWarnings(value)).toEqual([
      "There are more slots than hand-picked creators, so some slots can't be filled.",
    ]);
  });

  it("flags a missing angle list and a missing paid label", () => {
    const value = parsed(
      campaign((v) => {
        v.angles = [];
        v.paidLabelRequired = false;
      }),
    );
    expect(campaignWarnings(value)).toEqual([
      "No angles yet. Posts tend to sound alike without them.",
      "The paid partnership label is off. X requires it on paid posts.",
    ]);
  });

  it("flags a post window under an hour", () => {
    const value = parsed(
      campaign((v) => {
        v.timing.postWindowEnd = "2026-11-03T16:45:00Z";
      }),
    );
    expect(campaignWarnings(value)).toEqual(["The post window is under an hour. Creators in other time zones may miss it."]);
  });

  it("flags a quote target that isn't an X post", () => {
    const value = parsed(campaign((v) => (v.links.targetPostUrl = "https://nebula.example/launch")));
    expect(campaignWarnings(value)).toEqual([
      "The post to quote or reply to doesn't look like an X post link (x.com/name/status/...).",
    ]);
    const twitter = parsed(campaign((v) => (v.links.targetPostUrl = "https://twitter.com/nebula_ai/status/1975")));
    expect(campaignWarnings(twitter)).toEqual([]);
  });
});

describe("demo campaigns", () => {
  const holdsSlot = new Set(["claimed", "draft_submitted", "changes_requested", "draft_approved", "proof_submitted", "approved", "rejected", "paid"]);

  it("open as valid forms for Edit and Duplicate", () => {
    for (const demo of demoCampaigns) {
      const edit = makeCampaignSchema(() => NOW, { alreadyDropped: hasDropped(demo.status) });
      expect(failedPaths(campaignToFormInput(demo, "edit"), edit), demo.id).toEqual([]);
      // A duplicate starts with empty times, so only the timing step is left to fill.
      const duplicatePaths = failedPaths(campaignToFormInput(demo, "duplicate"));
      expect(duplicatePaths.every((path) => path.startsWith("timing.")), demo.id).toBe(true);
    }
  });

  it("have rosters that match their slot counts", () => {
    for (const demo of demoCampaigns) {
      const roster = demoRosters[demo.id] ?? [];
      expect(roster.filter((row) => holdsSlot.has(row.status)).length, demo.id).toBe(demo.slotsTaken);
      expect(roster.filter((row) => row.status === "requested").length, demo.id).toBe(demo.requests);
      expect(demo.slotsTaken, demo.id).toBeLessThanOrEqual(demo.slots);
    }
  });

  it("mark only paid claims as paid", () => {
    for (const rows of Object.values(demoRosters)) {
      for (const row of rows) expect(row.paid).toBe(row.status === "paid");
    }
  });
});
