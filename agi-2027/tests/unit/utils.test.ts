import { describe, expect, it } from "vitest";

import { cn } from "@/lib/utils";

describe("cn", () => {
  it("keeps the type scale apart from text colors", () => {
    expect(cn("text-h2 text-muted-foreground")).toBe("text-h2 text-muted-foreground");
    expect(cn("text-label text-brand-text")).toBe("text-label text-brand-text");
  });

  it("lets a later size replace an earlier one", () => {
    expect(cn("text-h2", "text-h3")).toBe("text-h3");
    expect(cn("text-h3", "text-xl")).toBe("text-xl");
  });

  it("keeps text-figure next to a size, since it sets none itself", () => {
    expect(cn("text-figure text-xl")).toBe("text-figure text-xl");
    expect(cn("text-figure", "text-[2rem]")).toBe("text-figure text-[2rem]");
  });
});
