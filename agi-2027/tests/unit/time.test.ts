import { describe, expect, it } from "vitest";

import { formatCountdown, formatDateTime, formatUtcTime } from "@/lib/time";

describe("formatCountdown", () => {
  it("shows days and hours when more than a day is left", () => {
    expect(formatCountdown((2 * 24 + 4) * 3_600_000 + 59_000)).toBe("2d 4h");
  });

  it("shows hours and padded minutes under a day", () => {
    expect(formatCountdown(4 * 3_600_000 + 5 * 60_000)).toBe("4h 05m");
  });

  it("shows minutes and padded seconds under an hour", () => {
    expect(formatCountdown(12 * 60_000 + 5_000)).toBe("12m 05s");
  });

  it("never rounds up past the time that is left", () => {
    expect(formatCountdown(59_999)).toBe("0m 59s");
  });

  it("reads 0s once the time has passed", () => {
    expect(formatCountdown(0)).toBe("0s");
    expect(formatCountdown(-5_000)).toBe("0s");
  });
});

describe("formatDateTime", () => {
  it("formats in the requested time zone with a fixed pattern", () => {
    expect(formatDateTime("2027-01-12T17:00:00Z", "UTC")).toBe("Tue 12 Jan, 17:00");
    expect(formatDateTime("2027-01-12T17:00:00Z", "Africa/Lagos")).toBe("Tue 12 Jan, 18:00");
  });

  it("shows midnight as 00:00, not 24:00", () => {
    expect(formatDateTime("2027-01-13T00:00:00Z", "UTC")).toBe("Wed 13 Jan, 00:00");
  });

  it("crosses the date line correctly", () => {
    expect(formatDateTime("2027-01-12T23:30:00Z", "Asia/Tokyo")).toBe("Wed 13 Jan, 08:30");
  });
});

describe("formatUtcTime", () => {
  it("returns the UTC clock time", () => {
    expect(formatUtcTime("2027-01-12T17:05:00+01:00")).toBe("16:05 UTC");
  });
});
