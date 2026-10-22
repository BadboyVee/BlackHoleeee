import { describe, expect, it } from "vitest";

import { sampleDataAllowed, showSampleData } from "@/lib/sample-data";

describe("sample data switch", () => {
  it("never shows samples on the live site", () => {
    expect(sampleDataAllowed({ live: true, supabase: true })).toBe(false);
    expect(sampleDataAllowed({ live: true, supabase: false })).toBe(false);
  });

  it("shows real data wherever a database is connected", () => {
    expect(sampleDataAllowed({ live: false, supabase: true })).toBe(false);
  });

  it("shows samples on preview links and laptops with no database", () => {
    expect(sampleDataAllowed({ live: false, supabase: false })).toBe(true);
  });

  it("is on in the test run, which has neither", () => {
    expect(showSampleData()).toBe(true);
  });
});
