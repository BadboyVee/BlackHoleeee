import { describe, expect, it } from "vitest";

import { adminNavGroupsFor, adminTabsFor, crumbsFor } from "@/components/admin/admin-nav";
import { buildItems } from "@/components/admin/command-palette";
import { adminCampaign, adminCampaignParams } from "@/components/admin/campaigns/visible";
import { oldestWaiting, overviewCounts } from "@/components/admin/overview/live-counts";
import { demoCampaigns } from "@/lib/campaigns/demo";
import { buildCreatorWorld, creatorCampaignFor, creatorCampaignIds, creatorCampaignParams } from "@/lib/campaigns/demo-creator";
import { demoApplications, demoSignups } from "@/lib/creators/demo";

/*
 * The live site never shows sample campaigns, claims, counts or people
 * (owner's request, 22 Oct 2026). Preview links keep every sample.
 */

const someCampaign = demoCampaigns[0]!.id;

describe("live site: admin", () => {
  it("puts no sample counts in the menu or the phone tabs", () => {
    const counts = (showSamples: boolean) =>
      [...adminNavGroupsFor(showSamples).flatMap((group) => group.items), ...adminTabsFor(showSamples)]
        .map((item) => item.count)
        .filter(Boolean);
    expect(counts(false)).toEqual([]);
    expect(counts(true).length).toBeGreaterThan(0);
  });

  it("names no sample campaign in the breadcrumbs", () => {
    expect(crumbsFor(`/admin/campaigns/${someCampaign}`, false)).toEqual([
      { label: "Campaigns", href: "/admin/campaigns" },
      { label: "Campaign" },
    ]);
    expect(crumbsFor(`/admin/campaigns/${someCampaign}`, true)[1]?.label).toBe(demoCampaigns[0]!.title);
  });

  it("leaves sample campaigns and builder actions out of search", () => {
    const live = buildItems(false);
    expect(live.some((item) => item.group === "Campaigns")).toBe(false);
    expect(live.some((item) => item.id === "action-new" || item.id === "action-duplicate")).toBe(false);
    expect(live.some((item) => item.group === "Pages")).toBe(true);
    expect(buildItems(true).filter((item) => item.group === "Campaigns")).toHaveLength(demoCampaigns.length);
  });

  it("opens no campaign, and prerenders one placeholder that is Not found", () => {
    expect(adminCampaign(someCampaign, false)).toBeUndefined();
    expect(adminCampaignParams(false)).toEqual([{ id: "none" }]);
    expect(adminCampaign(someCampaign, true)?.id).toBe(someCampaign);
    expect(adminCampaignParams(true)).toHaveLength(demoCampaigns.length);
  });

  it("counts only real applications and sign ups on the overview", () => {
    expect(overviewCounts(demoApplications, demoSignups)).toEqual({ waiting: 2, approved: 2, notApplied: 2 });
    expect(overviewCounts([], [])).toEqual({ waiting: 0, approved: 0, notApplied: 0 });
    expect(oldestWaiting(demoApplications).map((row) => row.id)).toEqual(["demo-app-2", "demo-app-1"]);
    expect(oldestWaiting(demoApplications, 1)).toHaveLength(1);
  });
});

describe("live site: creator portal", () => {
  it("hands every screen an empty world", () => {
    const world = buildCreatorWorld(false);
    expect(world.campaigns).toEqual([]);
    expect(world.claims).toEqual([]);
    expect(world.me.firstName).toBe("there");
    const preview = buildCreatorWorld(true);
    expect(preview.campaigns.length).toBeGreaterThan(0);
    expect(preview.claims.length).toBeGreaterThan(0);
  });

  it("opens no campaign, and prerenders one placeholder that is Not found", () => {
    const [id] = creatorCampaignIds();
    expect(creatorCampaignFor(id!, false)).toBeUndefined();
    expect(creatorCampaignParams(false)).toEqual([{ id: "none" }]);
    expect(creatorCampaignFor(id!, true)?.id).toBe(id);
  });
});
