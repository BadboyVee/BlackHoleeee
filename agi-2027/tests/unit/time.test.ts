import { describe, expect, it } from "vitest";

import { formatCountdown, formatDateTime, formatRange, formatTime, formatUtcDate, formatUtcDay, formatUtcTime } from "@/lib/time";

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

describe("formatTime", () => {
  it("returns the clock time in the given zone", () => {
    expect(formatTime("2026-11-03T16:00:00Z", "Africa/Lagos")).toBe("17:00");
  });
});

describe("formatRange", () => {
  it("shows the end time only when the range stays on one day", () => {
    expect(formatRange("2026-11-03T16:00:00Z", "2026-11-03T20:00:00Z", "UTC")).toBe(
      "Tue 3 Nov, 16:00 to 20:00",
    );
  });

  it("shows both dates when the range crosses midnight", () => {
    expect(formatRange("2026-11-07T14:00:00Z", "2026-11-08T14:00:00Z", "UTC")).toBe(
      "Sat 7 Nov, 14:00 to Sun 8 Nov, 14:00",
    );
  });

  it("uses the viewer's zone, which can move the range across days", () => {
    expect(formatRange("2026-11-03T22:00:00Z", "2026-11-03T23:30:00Z", "Asia/Tokyo")).toBe(
      "Wed 4 Nov, 07:00 to 08:30",
    );
  });
});

describe("formatUtcDate", () => {
  it("gives the calendar date in UTC with a fixed month name", () => {
    expect(formatUtcDate("2026-09-30T14:59:39Z")).toBe("30 Sep 2026");
    expect(formatUtcDate("2026-10-03T23:30:00-05:00")).toBe("4 Oct 2026");
  });
});

describe("formatUtcDay", () => {
  it("gives the weekday and date in UTC with fixed names, never Intl's", () => {
    expect(formatUtcDay("2026-09-30T14:59:39Z")).toBe("Wed 30 Sep");
    expect(formatUtcDay(new Date("2026-09-30T15:00:00Z"))).toBe("Wed 30 Sep");
  });

  it("takes the UTC day when an offset moves the time across midnight", () => {
    // 23:30 in New York on Saturday 3 Oct is 04:30 UTC on Sunday 4 Oct.
    expect(formatUtcDay("2026-10-03T23:30:00-05:00")).toBe("Sun 4 Oct");
    // 00:30 in Paris on 1 Jan 2027 is still 31 Dec 2026 in UTC.
    expect(formatUtcDay("2027-01-01T00:30:00+01:00")).toBe("Thu 31 Dec");
  });
});
