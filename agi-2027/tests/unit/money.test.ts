import { describe, expect, it } from "vitest";

import { formatMoney, splitMoney, totalsByCurrency } from "@/lib/money";

describe("formatMoney", () => {
  it("uses the currency symbol for fiat currencies", () => {
    expect(formatMoney("250", "USD")).toBe("$250");
    expect(formatMoney("250.5", "USD")).toBe("$250.50");
    expect(formatMoney(180000, "NGN")).toBe("₦180,000");
  });

  it("puts the code after the number for stablecoins", () => {
    expect(formatMoney("250", "USDC")).toBe("250 USDC");
    expect(formatMoney("1250.75", "USDT")).toBe("1,250.75 USDT");
  });
});

describe("totalsByCurrency", () => {
  it("keeps each currency separate", () => {
    expect(
      totalsByCurrency([
        { amount: "100", currency: "USD" },
        { amount: "50000", currency: "NGN" },
        { amount: "25.50", currency: "USD" },
      ]),
    ).toEqual([
      { currency: "USD", amount: "125.50" },
      { currency: "NGN", amount: "50000.00" },
    ]);
  });

  it("adds exactly, without floating point drift", () => {
    expect(
      totalsByCurrency([
        { amount: "0.1", currency: "USDC" },
        { amount: "0.2", currency: "USDC" },
      ]),
    ).toEqual([{ currency: "USDC", amount: "0.30" }]);
  });

  it("subtracts deductions", () => {
    expect(
      totalsByCurrency([
        { amount: "200", currency: "USD" },
        { amount: "-35.25", currency: "USD" },
      ]),
    ).toEqual([{ currency: "USD", amount: "164.75" }]);
  });

  it("goes negative when deductions exceed earnings", () => {
    expect(totalsByCurrency([{ amount: "-0.5", currency: "USD" }])).toEqual([
      { currency: "USD", amount: "-0.50" },
    ]);
  });

  it("rejects amounts that aren't plain decimals", () => {
    expect(() => totalsByCurrency([{ amount: "1e3", currency: "USD" }])).toThrow();
    expect(() => totalsByCurrency([{ amount: "12.345", currency: "USD" }])).toThrow();
  });
});

describe("splitMoney", () => {
  it("keeps the symbol in the number for fiat", () => {
    expect(splitMoney("400", "USD")).toEqual({ value: "$400" });
    expect(splitMoney("180000", "NGN")).toEqual({ value: "₦180,000" });
  });

  it("splits stablecoins into the number and a unit", () => {
    expect(splitMoney("250", "USDC")).toEqual({ value: "250", unit: "USDC" });
    expect(splitMoney("1250.5", "USDT")).toEqual({ value: "1,250.50", unit: "USDT" });
  });
});
