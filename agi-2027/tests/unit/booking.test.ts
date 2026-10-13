import { describe, expect, it } from "vitest";

import {
  BUDGET_RANGES,
  bookingSchema,
  budgetLabel,
  HONEYPOT_FIELD,
  LIMITS,
  normalizeWebsite,
  normalizeXHandle,
  type BookingFormValues,
} from "@/lib/leads/booking";

const valid: BookingFormValues = {
  name: "Ada Lovelace",
  email: "ada@kled.ai",
  company: "Kled",
  website: "kled.ai",
  xHandle: "@kled_ai",
  launching: "An AI data marketplace, launching on X.",
  launchDate: "2026-11-12",
  budget: "10k_25k",
  message: "We want ten creators in the first week.",
};

/** The first error message for a field, or undefined when the field passed. */
function errorFor(values: Partial<BookingFormValues>, field: keyof BookingFormValues) {
  const result = bookingSchema.safeParse({ ...valid, ...values });
  if (result.success) return undefined;
  return result.error.issues.find((issue) => issue.path[0] === field)?.message;
}

describe("bookingSchema", () => {
  it("accepts a full booking and normalizes it", () => {
    const result = bookingSchema.parse(valid);
    expect(result).toEqual({
      name: "Ada Lovelace",
      email: "ada@kled.ai",
      company: "Kled",
      website: "https://kled.ai",
      xHandle: "kled_ai",
      launching: "An AI data marketplace, launching on X.",
      launchDate: "2026-11-12",
      budget: "10k_25k",
      message: "We want ten creators in the first week.",
    });
  });

  it("accepts a booking with only the required fields", () => {
    const result = bookingSchema.parse({
      name: "Ada",
      email: "ada@kled.ai",
      company: "Kled",
      launching: "A launch on X next month.",
      budget: "not_sure",
    });
    expect(result.website).toBeUndefined();
    expect(result.xHandle).toBeUndefined();
    expect(result.launchDate).toBeUndefined();
    expect(result.message).toBeUndefined();
  });

  it("turns empty optional fields into undefined", () => {
    const result = bookingSchema.parse({ ...valid, website: "  ", xHandle: "", launchDate: "", message: "   " });
    expect(result.website).toBeUndefined();
    expect(result.xHandle).toBeUndefined();
    expect(result.launchDate).toBeUndefined();
    expect(result.message).toBeUndefined();
  });

  it("trims every text field", () => {
    const result = bookingSchema.parse({
      ...valid,
      name: "  Ada  ",
      email: " ada@kled.ai ",
      company: "\tKled\n",
      launching: "  An AI data marketplace.  ",
      message: "  Hello  ",
    });
    expect(result.name).toBe("Ada");
    expect(result.email).toBe("ada@kled.ai");
    expect(result.company).toBe("Kled");
    expect(result.launching).toBe("An AI data marketplace.");
    expect(result.message).toBe("Hello");
  });

  it("accepts every budget range", () => {
    for (const range of BUDGET_RANGES) {
      expect(bookingSchema.safeParse({ ...valid, budget: range.value }).success).toBe(true);
    }
  });

  describe("rejects", () => {
    it("a missing or blank name", () => {
      expect(errorFor({ name: "" }, "name")).toBe("Tell us your name.");
      expect(errorFor({ name: "   " }, "name")).toBe("Tell us your name.");
    });

    it("a name over the limit", () => {
      expect(errorFor({ name: "a".repeat(LIMITS.name + 1) }, "name")).toBe(`Keep it under ${LIMITS.name} characters.`);
      expect(errorFor({ name: "a".repeat(LIMITS.name) }, "name")).toBeUndefined();
    });

    it("a bad email", () => {
      expect(errorFor({ email: "" }, "email")).toBe("Enter an email we can reply to.");
      expect(errorFor({ email: "ada" }, "email")).toBe("Enter an email we can reply to.");
      expect(errorFor({ email: "ada@" }, "email")).toBe("Enter an email we can reply to.");
      expect(errorFor({ email: "ada @kled.ai" }, "email")).toBe("Enter an email we can reply to.");
    });

    it("an email over the limit", () => {
      expect(errorFor({ email: `${"a".repeat(LIMITS.email)}@kled.ai` }, "email")).toBeDefined();
    });

    it("a missing or long company", () => {
      expect(errorFor({ company: "" }, "company")).toBe("Which company is launching?");
      expect(errorFor({ company: "a".repeat(LIMITS.company + 1) }, "company")).toBe(
        `Keep it under ${LIMITS.company} characters.`,
      );
    });

    it("a website that isn't a web address", () => {
      for (const website of ["not a site", "javascript:alert(1)", "ftp://kled.ai", "localhost", "https://kled"]) {
        expect(errorFor({ website }, "website")).toBe("Enter a website like example.com.");
      }
    });

    it("a website that only grows past the limit once it's cleaned up", () => {
      // Short enough as typed, but https:// and percent-encoding make it longer than the database allows.
      const withoutScheme = `kled.ai/${"a".repeat(LIMITS.website - "kled.ai/".length)}`;
      const nonAscii = `kled.ai/${"é".repeat(400)}`;
      for (const website of [withoutScheme, nonAscii]) {
        expect(website.length).toBeLessThanOrEqual(LIMITS.website);
        expect(errorFor({ website }, "website")).toBe("That link is too long. The domain alone is fine.");
      }
      const longest = `https://kled.ai/${"a".repeat(LIMITS.website - "https://kled.ai/".length)}`;
      expect(bookingSchema.parse({ ...valid, website: longest }).website).toHaveLength(LIMITS.website);
    });

    it("an X handle that can't exist", () => {
      for (const xHandle of ["@has space", "@this_handle_is_too_long", "kled.ai", "@"]) {
        expect(errorFor({ xHandle }, "xHandle")).toBe("Enter an X handle like @yourcompany.");
      }
    });

    it("a launch description that's too short or too long", () => {
      expect(errorFor({ launching: "" }, "launching")).toBe("A sentence or two about what you're launching.");
      expect(errorFor({ launching: "An app" }, "launching")).toBe("A sentence or two about what you're launching.");
      expect(errorFor({ launching: "a".repeat(LIMITS.launching + 1) }, "launching")).toBe(
        `Keep it under ${LIMITS.launching} characters.`,
      );
    });

    it("a launch date that isn't a date", () => {
      const notDates = ["12/11/2026", "2026-13-01", "soon", "2026-11-1", "2026-02-31", "2027-02-29", "0000-01-01"];
      for (const launchDate of notDates) {
        expect(errorFor({ launchDate }, "launchDate")).toBe("Pick a date, or leave it empty.");
      }
    });

    it("a missing or unknown budget", () => {
      expect(errorFor({ budget: "" as never }, "budget")).toBe("Pick a budget range.");
      expect(errorFor({ budget: "a_million" as never }, "budget")).toBe("Pick a budget range.");
    });

    it("a message over the limit", () => {
      expect(errorFor({ message: "a".repeat(LIMITS.message + 1) }, "message")).toBe(
        `Keep it under ${LIMITS.message} characters.`,
      );
    });
  });
});

describe("normalizeWebsite", () => {
  it("adds https and drops the trailing slash", () => {
    expect(normalizeWebsite("kled.ai")).toBe("https://kled.ai");
    expect(normalizeWebsite("https://kled.ai/")).toBe("https://kled.ai");
    expect(normalizeWebsite("  KLED.ai  ")).toBe("https://kled.ai");
  });

  it("keeps http, paths and queries", () => {
    expect(normalizeWebsite("http://kled.ai")).toBe("http://kled.ai");
    expect(normalizeWebsite("kled.ai/launch/")).toBe("https://kled.ai/launch");
    expect(normalizeWebsite("https://www.kled.ai/a?ref=x")).toBe("https://www.kled.ai/a?ref=x");
  });

  it("refuses anything that isn't an http(s) link on a real domain", () => {
    expect(normalizeWebsite("")).toBeNull();
    expect(normalizeWebsite("   ")).toBeNull();
    expect(normalizeWebsite("javascript:alert(1)")).toBeNull();
    expect(normalizeWebsite("mailto:ada@kled.ai")).toBeNull();
    expect(normalizeWebsite("ftp://kled.ai")).toBeNull();
    expect(normalizeWebsite("https://user:pass@kled.ai")).toBeNull();
    expect(normalizeWebsite("https://localhost")).toBeNull();
    expect(normalizeWebsite("https://127.0.0.1")).toBeNull();
    expect(normalizeWebsite("not a site")).toBeNull();
  });
});

describe("normalizeXHandle", () => {
  it("strips the @ and keeps the case", () => {
    expect(normalizeXHandle("@Kled_AI")).toBe("Kled_AI");
    expect(normalizeXHandle("kled_ai")).toBe("kled_ai");
    expect(normalizeXHandle("  @kled  ")).toBe("kled");
  });

  it("reads the handle out of a profile link", () => {
    expect(normalizeXHandle("x.com/kled_ai")).toBe("kled_ai");
    expect(normalizeXHandle("https://x.com/kled_ai?s=20")).toBe("kled_ai");
    expect(normalizeXHandle("https://twitter.com/@kled_ai/")).toBe("kled_ai");
    expect(normalizeXHandle("https://mobile.twitter.com/kled_ai")).toBe("kled_ai");
  });

  it("refuses handles X wouldn't allow", () => {
    expect(normalizeXHandle("")).toBeNull();
    expect(normalizeXHandle("@")).toBeNull();
    expect(normalizeXHandle("has space")).toBeNull();
    expect(normalizeXHandle("sixteen_chars_xx")).toBeNull();
    expect(normalizeXHandle("kled.ai")).toBeNull();
    expect(normalizeXHandle("<script>")).toBeNull();
  });
});

describe("budgetLabel", () => {
  it("labels every range and passes unknown values through", () => {
    expect(budgetLabel("under_5k")).toBe("Under $5k");
    expect(budgetLabel("10k_25k")).toBe("$10k to $25k");
    expect(budgetLabel("not_sure")).toBe("Not sure yet");
    expect(budgetLabel("mystery")).toBe("mystery");
  });
});

describe("HONEYPOT_FIELD", () => {
  it("has a name no browser autofill or password manager would fill", () => {
    // Autofill fills fields by name. If it filled the trap, a real person's booking
    // would get the bot's fake thank-you and never be saved.
    const autofillWords =
      /name|mail|company|organi[sz]ation|org|business|phone|tel|fax|address|street|city|state|zip|postal|country|url|web|site|user|login|card|birth/i;
    expect(HONEYPOT_FIELD).not.toMatch(autofillWords);
    expect(Object.keys(valid)).not.toContain(HONEYPOT_FIELD);
  });
});
