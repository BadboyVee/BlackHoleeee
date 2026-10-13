import { describe, expect, expectTypeOf, it } from "vitest";

import { demoCampaigns, type DemoCampaign } from "@/lib/campaigns/demo";
import {
  DEMO_BOARD_NOW,
  publicCampaigns,
  publicCampaignSignupHref,
  type PublicCampaign,
} from "@/lib/campaigns/public";

const NOW = new Date(DEMO_BOARD_NOW);

const SAFE_KEYS = [
  "brand",
  "claimMode",
  "deliverable",
  "droppedAt",
  "id",
  "platform",
  "postWindow",
  "slots",
  "status",
  "summary",
  "title",
];

/** Words that must never reach the public board, at any depth. */
const FORBIDDEN = ["payout", "budget", "notes", "internal", "audience", "roster", "tier", "creatorPayouts", "brief", "links", "requests"];

/** A live, all-creators demo campaign to vary in each test. */
function campaign(overrides: Partial<DemoCampaign> = {}): DemoCampaign {
  const base = structuredClone(demoCampaigns.find((item) => item.id === "cmp-nebula-2")!);
  return { ...base, ...overrides };
}

function allKeys(value: unknown, path = ""): string[] {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value).flatMap(([key, child]) => [`${path}${key}`, ...allKeys(child, `${path}${key}.`)]);
}

describe("publicCampaigns on the demo data", () => {
  const board = publicCampaigns(NOW);

  it("shows only open, all-creator campaigns, newest drop first", () => {
    expect(board.map((item) => item.id)).toEqual(["cmp-quill-agent", "cmp-orbitar-beta", "cmp-nebula-2"]);
    for (const item of board) expect(["live", "full"]).toContain(item.status);
  });

  it("never shows tier, tag or hand-picked campaigns", () => {
    const ids = board.map((item) => item.id);
    // Tags, tiers (and full), hand-picked (and scheduled).
    expect(ids).not.toContain("cmp-lumen-weights");
    expect(ids).not.toContain("cmp-vectorline-a");
    expect(ids).not.toContain("cmp-quill-founder");
  });

  it("never shows drafts, paused, closed or finished campaigns", () => {
    const ids = board.map((item) => item.id);
    for (const id of ["cmp-nebula-draft", "cmp-lumen-code", "cmp-vectorline-bench", "cmp-orbitar-alpha"]) {
      expect(ids).not.toContain(id);
    }
  });

  it("carries only the safe fields, at runtime", () => {
    for (const item of board) {
      expect(Object.keys(item).sort()).toEqual(SAFE_KEYS);
      expect(Object.keys(item.brand).sort()).toEqual(["color", "initials", "name"]);
      expect(Object.keys(item.slots).sort()).toEqual(["taken", "total"]);
      expect(Object.keys(item.postWindow).sort()).toEqual(["end", "start"]);
      for (const key of allKeys(item)) {
        for (const word of FORBIDDEN) expect(key.toLowerCase()).not.toContain(word.toLowerCase());
      }
    }
  });

  it("leaks no payout or budget amounts", () => {
    const text = JSON.stringify(board);
    for (const source of demoCampaigns) {
      expect(text).not.toContain(`"${source.payout.amount}"`);
      if (source.internal.budgetAmount) expect(text).not.toContain(`"${source.internal.budgetAmount}"`);
      if (source.internal.notes) expect(text).not.toContain(source.internal.notes);
    }
  });

  it("has only safe fields at the type level", () => {
    expectTypeOf<keyof PublicCampaign>().toEqualTypeOf<
      | "id"
      | "brand"
      | "title"
      | "summary"
      | "platform"
      | "deliverable"
      | "postWindow"
      | "slots"
      | "status"
      | "claimMode"
      | "droppedAt"
    >();
    expectTypeOf<keyof PublicCampaign["brand"]>().toEqualTypeOf<"name" | "initials" | "color">();
  });
});

describe("publicCampaigns rules", () => {
  it("keeps live campaigns open to all creators", () => {
    expect(publicCampaigns(NOW, [campaign()])).toHaveLength(1);
  });

  it("drops every audience except all creators", () => {
    const source = [
      campaign({ id: "tiers", audience: { kind: "tiers", tiers: ["Tier 1"], tags: [], creatorIds: [] } }),
      campaign({ id: "tags", audience: { kind: "tags", tiers: [], tags: ["Crypto"], creatorIds: [] } }),
      campaign({ id: "picked", audience: { kind: "creators", tiers: [], tags: [], creatorIds: ["u-amara"] } }),
    ];
    expect(publicCampaigns(NOW, source)).toEqual([]);
  });

  it("drops anything that isn't live or full", () => {
    const statuses = ["draft", "scheduled", "paused", "closed", "completed"] as const;
    const source = statuses.map((status) => campaign({ id: status, status }));
    expect(publicCampaigns(NOW, source)).toEqual([]);
  });

  it("turns Live into Full when the last slot goes, and back", () => {
    const [full, reopened] = publicCampaigns(NOW, [
      campaign({ id: "a", slots: 5, slotsTaken: 5, droppedAt: "2026-11-02T00:00:00Z" }),
      campaign({ id: "b", status: "full", slots: 5, slotsTaken: 4, droppedAt: "2026-11-01T00:00:00Z" }),
    ]);
    expect(full).toMatchObject({ id: "a", status: "full", slots: { total: 5, taken: 5 } });
    expect(reopened).toMatchObject({ id: "b", status: "live", slots: { total: 5, taken: 4 } });
  });

  it("hides drops that aren't out yet and windows that have ended", () => {
    const later = campaign({ id: "later", droppedAt: "2026-11-03T19:00:01Z" });
    const over = campaign({
      id: "over",
      timing: { ...campaign().timing, postWindowEnd: DEMO_BOARD_NOW },
    });
    expect(publicCampaigns(NOW, [later, over])).toEqual([]);
  });

  it("sorts newest drop first, falling back to the creation time", () => {
    const source = [
      campaign({ id: "old", droppedAt: "2026-10-01T00:00:00Z" }),
      campaign({ id: "newest", droppedAt: "2026-11-02T00:00:00Z" }),
      campaign({ id: "created", droppedAt: undefined, createdAt: "2026-10-15T00:00:00Z" }),
    ];
    const board = publicCampaigns(NOW, source);
    expect(board.map((item) => item.id)).toEqual(["newest", "created", "old"]);
    expect(board[1].droppedAt).toBe("2026-10-15T00:00:00Z");
  });

  it("builds new objects instead of passing the source through", () => {
    const source = campaign();
    const [item] = publicCampaigns(NOW, [source]);
    expect(item).not.toBe(source);
    expect(item.postWindow).toEqual({ start: source.timing.postWindowStart, end: source.timing.postWindowEnd });
  });
});

describe("publicCampaignSignupHref", () => {
  it("signs up, then opens that campaign", () => {
    expect(publicCampaignSignupHref("cmp-nebula-2")).toBe("/signup?next=/dashboard/campaigns/cmp-nebula-2");
  });

  it("can't be steered elsewhere by an odd id", () => {
    expect(publicCampaignSignupHref("x&next=https://evil.example")).toBe(
      "/signup?next=/dashboard/campaigns/x%26next%3Dhttps%3A%2F%2Fevil.example",
    );
  });
});
