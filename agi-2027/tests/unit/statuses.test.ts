import { describe, expect, it } from "vitest";

import {
  CAMPAIGN_STATUSES,
  CLAIM_STATUSES,
  campaignStatusMeta,
  claimStatusMeta,
  statusMeta,
  TONES,
} from "@/lib/statuses";

describe("status metadata", () => {
  it("covers every claim status from the spec", () => {
    expect(Object.keys(claimStatusMeta).sort()).toEqual([...CLAIM_STATUSES].sort());
    expect(CLAIM_STATUSES).toHaveLength(11);
  });

  it("covers every campaign status from the spec", () => {
    expect(Object.keys(campaignStatusMeta).sort()).toEqual([...CAMPAIGN_STATUSES].sort());
    expect(CAMPAIGN_STATUSES).toHaveLength(7);
  });

  it("uses known tones and unique labels within each kind", () => {
    for (const metas of Object.values(statusMeta)) {
      const labels = Object.values(metas).map((meta) => meta.label);
      expect(new Set(labels).size).toBe(labels.length);
      for (const meta of Object.values(metas)) {
        expect(TONES).toContain(meta.tone);
        expect(meta.description.length).toBeGreaterThan(0);
      }
    }
  });
});
