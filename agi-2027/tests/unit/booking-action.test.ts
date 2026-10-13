import { createHash } from "node:crypto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { isCalendarDate, MIN_FILL_MS, type BookingState } from "@/lib/leads/booking";
import {
  classifySubmitError,
  FIELDS_MESSAGE,
  fillTimeMessage,
  fillTimeProblem,
  firstFieldErrors,
  honeypotFilled,
  readBookingValues,
  submitErrorMessage,
  type SubmitLeadResult,
} from "@/lib/leads/errors";

const mocks = vi.hoisted(() => ({
  headers: vi.fn(async () => new Headers()),
  after: vi.fn(),
  submitLead: vi.fn(),
  deliverOutbox: vi.fn(),
  site: { name: "AGI 2027", url: "https://agi2027.test", contactEmail: "" },
}));

vi.mock("next/headers", () => ({ headers: mocks.headers }));
vi.mock("next/server", () => ({ after: mocks.after }));
vi.mock("@/lib/leads/submit", () => ({ submitLead: mocks.submitLead }));
vi.mock("@/lib/outbox/deliver", () => ({ deliverOutbox: mocks.deliverOutbox }));
vi.mock("@/lib/site", () => ({ siteConfig: mocks.site }));

const { submitBooking } = await import("@/app/(marketing)/book/actions");

const NOW = new Date("2026-10-12T17:00:00Z").getTime();
const DAY = 24 * 60 * 60 * 1000;
const DASHES = /[\u2013\u2014]/;
const idle: BookingState = { status: "idle" };

const fields = {
  name: "  Ada Lovelace ",
  email: " ada@kled.ai ",
  company: "Kled",
  website: "kled.ai/",
  xHandle: "@kled_ai",
  launching: "An AI data marketplace, launching on X.",
  launchDate: "2026-11-12",
  budget: "10k_25k",
  message: "",
};

/** The form as the browser sends it: a human who took a minute, from the home page. */
function form(overrides: Record<string, string | null> = {}) {
  const data = new FormData();
  const all: Record<string, string | null> = {
    ...fields,
    source: "home_cta",
    company_site: "",
    started_at: String(NOW - 60_000),
    ...overrides,
  };
  for (const [key, value] of Object.entries(all)) {
    if (value !== null) data.set(key, value);
  }
  return data;
}

const saved: SubmitLeadResult = { ok: true, leadId: "lead-1", outboxId: "outbox-1" };

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  vi.stubEnv("RATE_LIMIT_SALT", "pepper");
  mocks.headers.mockResolvedValue(new Headers({ "x-forwarded-for": "203.0.113.7, 10.0.0.1" }));
  mocks.submitLead.mockResolvedValue(saved);
  mocks.deliverOutbox.mockResolvedValue({ claimed: 1, sent: 1, failed: 0 });
  mocks.site.contactEmail = "";
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  mocks.after.mockReset();
  mocks.submitLead.mockReset();
  mocks.deliverOutbox.mockReset();
  mocks.headers.mockReset();
});

describe("submitBooking", () => {
  it("saves a good booking, answers with the clean name and email, and sends the email afterwards", async () => {
    const state = await submitBooking(idle, form());

    expect(state).toEqual({ status: "success", name: "Ada Lovelace", email: "ada@kled.ai" });
    expect(mocks.submitLead).toHaveBeenCalledTimes(1);
    const [booking, options] = mocks.submitLead.mock.calls[0];
    expect(booking).toEqual({
      name: "Ada Lovelace",
      email: "ada@kled.ai",
      company: "Kled",
      website: "https://kled.ai",
      xHandle: "kled_ai",
      launching: "An AI data marketplace, launching on X.",
      launchDate: "2026-11-12",
      budget: "10k_25k",
      message: undefined,
    });
    expect(options.source).toBe("home_cta");

    // Delivery waits for after(), so the response doesn't wait for Resend.
    expect(mocks.after).toHaveBeenCalledTimes(1);
    expect(mocks.deliverOutbox).not.toHaveBeenCalled();
    await mocks.after.mock.calls[0][0]();
    expect(mocks.deliverOutbox).toHaveBeenCalledWith({ id: "outbox-1", limit: 1 });
  });

  it("keeps the response a success when delivery fails later", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    mocks.deliverOutbox.mockRejectedValue(new Error("boom"));
    await submitBooking(idle, form());
    await expect(mocks.after.mock.calls[0][0]()).resolves.toBeUndefined();
  });

  describe("spam checks", () => {
    it("thanks a bot that fills the honeypot, and saves nothing", async () => {
      const state = await submitBooking(idle, form({ company_site: "https://spam.example" }));
      expect(state).toEqual({ status: "success", name: "Ada Lovelace", email: "ada@kled.ai" });
      expect(mocks.submitLead).not.toHaveBeenCalled();
      expect(mocks.after).not.toHaveBeenCalled();
    });

    it("checks the honeypot before anything else, even an invalid form", async () => {
      const state = await submitBooking(idle, form({ company_site: "x", started_at: null, email: "nope" }));
      expect(state.status).toBe("success");
      expect(mocks.submitLead).not.toHaveBeenCalled();
    });

    it("asks a form sent too fast to send again, keeping what was typed", async () => {
      const state = await submitBooking(idle, form({ started_at: String(NOW - 1000) }));
      expect(state).toEqual({
        status: "error",
        message: fillTimeMessage(""),
        values: expect.objectContaining({ name: "  Ada Lovelace ", company: "Kled" }),
      });
      expect(mocks.submitLead).not.toHaveBeenCalled();
    });

    it("refuses a missing, garbled or day-old timer", async () => {
      for (const started_at of [null, "", "soon", "1e12", String(NOW - DAY - 1)]) {
        const state = await submitBooking(idle, form({ started_at }));
        expect(state).toMatchObject({ status: "error", message: fillTimeMessage("") });
      }
      expect(mocks.submitLead).not.toHaveBeenCalled();
    });

    it("lets a visitor whose clock runs ahead through", async () => {
      const state = await submitBooking(idle, form({ started_at: String(NOW + 90_000) }));
      expect(state.status).toBe("success");
      expect(mocks.submitLead).toHaveBeenCalledTimes(1);
    });
  });

  describe("validation", () => {
    it("returns the first message per field and the values sent", async () => {
      const state = await submitBooking(
        idle,
        form({ name: "", email: "nope", website: "not a site", launching: "short", budget: "" }),
      );
      expect(state).toEqual({
        status: "error",
        message: FIELDS_MESSAGE,
        fieldErrors: {
          name: "Tell us your name.",
          email: "Enter an email we can reply to.",
          website: "Enter a website like example.com.",
          launching: "A sentence or two about what you're launching.",
          budget: "Pick a budget range.",
        },
        values: {
          ...fields,
          name: "",
          email: "nope",
          website: "not a site",
          launching: "short",
          budget: "",
        },
      });
      expect(mocks.submitLead).not.toHaveBeenCalled();
    });

    it("treats missing fields as empty, so people see friendly messages", async () => {
      const state = await submitBooking(idle, form({ name: null, email: null, company: null }));
      expect(state).toMatchObject({
        status: "error",
        fieldErrors: {
          name: "Tell us your name.",
          email: "Enter an email we can reply to.",
          company: "Which company is launching?",
        },
      });
    });

    it("refuses a launch date that isn't on the calendar", async () => {
      const state = await submitBooking(idle, form({ launchDate: "2026-02-31" }));
      expect(state).toMatchObject({
        status: "error",
        fieldErrors: { launchDate: "Pick a date, or leave it empty." },
      });
      expect(mocks.submitLead).not.toHaveBeenCalled();
    });
  });

  describe("source", () => {
    it("defaults to the book page when missing or unknown", async () => {
      await submitBooking(idle, form({ source: null }));
      await submitBooking(idle, form({ source: "admin" }));
      expect(mocks.submitLead.mock.calls.map(([, options]) => options.source)).toEqual(["book_page", "book_page"]);
    });
  });

  describe("rate key", () => {
    const hash = (value: string) => createHash("sha256").update(value).digest("hex");

    it("hashes the salt and the first forwarded IP", async () => {
      await submitBooking(idle, form());
      const { rateKey } = mocks.submitLead.mock.calls[0][1];
      expect(rateKey).toBe(hash("pepper203.0.113.7"));
      expect(rateKey).toMatch(/^[0-9a-f]{64}$/);
      expect(rateKey).not.toContain("203.0.113.7");
    });

    it("falls back to x-real-ip, then to 'unknown'", async () => {
      mocks.headers.mockResolvedValueOnce(new Headers({ "x-real-ip": "198.51.100.4" }));
      await submitBooking(idle, form());
      mocks.headers.mockResolvedValueOnce(new Headers());
      await submitBooking(idle, form());
      expect(mocks.submitLead.mock.calls.map(([, options]) => options.rateKey)).toEqual([
        hash("pepper198.51.100.4"),
        hash("pepperunknown"),
      ]);
    });

    it("on Netlify, uses only the address Netlify sets, never a forwarded one", async () => {
      vi.stubEnv("AGI_DEPLOY_HOST", "netlify");
      mocks.headers.mockResolvedValueOnce(
        new Headers({ "x-forwarded-for": "6.6.6.6", "x-nf-client-connection-ip": "192.0.2.10" }),
      );
      await submitBooking(idle, form());
      expect(mocks.submitLead.mock.calls[0][1].rateKey).toBe(hash("pepper192.0.2.10"));
    });

    it("uses a built-in salt without RATE_LIMIT_SALT, and warns once", async () => {
      vi.stubEnv("RATE_LIMIT_SALT", "");
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      vi.resetModules();
      const fresh = await import("@/app/(marketing)/book/actions");
      await fresh.submitBooking(idle, form());
      await fresh.submitBooking(idle, form());
      const keys = mocks.submitLead.mock.calls.map(([, options]) => options.rateKey);
      expect(keys[0]).toMatch(/^[0-9a-f]{64}$/);
      expect(keys[0]).toBe(keys[1]);
      expect(keys[0]).not.toBe(hash("203.0.113.7"));
      expect(warn).toHaveBeenCalledTimes(1);
      expect(String(warn.mock.calls[0][0])).toContain("RATE_LIMIT_SALT");
    });
  });

  describe("when saving fails", () => {
    it("tells a rate limited visitor to try again in an hour", async () => {
      mocks.submitLead.mockResolvedValue({ ok: false, reason: "rate_limited", code: "P0429" });
      const state = await submitBooking(idle, form());
      expect(state).toEqual({
        status: "error",
        message: "Too many requests from this connection. Try again in an hour, or email us.",
        values: expect.objectContaining({ company: "Kled" }),
      });
      expect(mocks.after).not.toHaveBeenCalled();
    });

    it("adds the contact email when there is one", async () => {
      mocks.site.contactEmail = "hello@agi2027.test";
      mocks.submitLead.mockResolvedValue({ ok: false, reason: "rate_limited", code: "P0429" });
      const state = await submitBooking(idle, form());
      expect(state).toMatchObject({
        message: "Too many requests from this connection. Try again in an hour, or email us at hello@agi2027.test.",
      });
    });

    it("says bookings aren't connected when Supabase isn't configured", async () => {
      mocks.site.contactEmail = "hello@agi2027.test";
      mocks.submitLead.mockResolvedValue({ ok: false, reason: "not_configured" });
      const state = await submitBooking(idle, form());
      expect(state.status).toBe("error");
      if (state.status !== "error") return;
      expect(state.message).toContain("aren't connected yet");
      expect(state.message).toContain("hello@agi2027.test");
      expect(state.values?.email).toBe(" ada@kled.ai ");
      expect(mocks.after).not.toHaveBeenCalled();
    });

    it("asks them to retry on any other failure", async () => {
      mocks.submitLead.mockResolvedValue({ ok: false, reason: "failed", code: "XX000" });
      const state = await submitBooking(idle, form());
      expect(state).toMatchObject({ status: "error", message: "We couldn't save that just now. Try again in a minute." });
    });
  });
});

describe("booking error helpers", () => {
  describe("classifySubmitError", () => {
    it("spots the rate limit by errcode or message", () => {
      expect(classifySubmitError({ code: "P0429", message: "rate_limited" })).toBe("rate_limited");
      expect(classifySubmitError({ code: "P0001", message: "rate_limited" })).toBe("rate_limited");
    });

    it("treats everything else as a failure", () => {
      expect(classifySubmitError({ code: "23514", message: "violates check constraint" })).toBe("failed");
      expect(classifySubmitError({ code: "PGRST202", message: "function not found" })).toBe("failed");
      expect(classifySubmitError(new Error("fetch failed"))).toBe("failed");
      expect(classifySubmitError(null)).toBe("failed");
      expect(classifySubmitError("P0429")).toBe("failed");
    });
  });

  describe("submitErrorMessage", () => {
    it("words each failure, with and without a contact email", () => {
      expect(submitErrorMessage("rate_limited", "")).toBe(
        "Too many requests from this connection. Try again in an hour, or email us.",
      );
      expect(submitErrorMessage("rate_limited", " hi@agi.test ")).toBe(
        "Too many requests from this connection. Try again in an hour, or email us at hi@agi.test.",
      );
      expect(submitErrorMessage("not_configured", "")).toBe(
        "Bookings aren't connected yet, so we couldn't save this. Please try again soon.",
      );
      expect(submitErrorMessage("not_configured", "hi@agi.test")).toBe(
        "Bookings aren't connected yet, so we couldn't save this. Email us at hi@agi.test and we'll reply.",
      );
      expect(submitErrorMessage("failed", "")).toBe("We couldn't save that just now. Try again in a minute.");
      expect(submitErrorMessage("failed", "hi@agi.test")).toBe(
        "We couldn't save that just now. Try again in a minute, or email us at hi@agi.test.",
      );
    });

    it("tells people who can't pass the spam timer, such as without JavaScript, how to reach us", () => {
      expect(fillTimeMessage(" hi@agi.test ")).toBe(
        "We couldn't check that send. Wait a few seconds and try again. If it keeps happening, turn on JavaScript or email us at hi@agi.test.",
      );
      expect(fillTimeMessage("")).toBe(
        "We couldn't check that send. Wait a few seconds and try again. If it keeps happening, turn on JavaScript.",
      );
    });

    it("never uses em or en dashes", () => {
      for (const reason of ["rate_limited", "not_configured", "failed"] as const) {
        expect(submitErrorMessage(reason, "")).not.toMatch(DASHES);
        expect(submitErrorMessage(reason, "hi@agi.test")).not.toMatch(DASHES);
      }
      expect(fillTimeMessage("")).not.toMatch(DASHES);
      expect(fillTimeMessage("hi@agi.test")).not.toMatch(DASHES);
      expect(FIELDS_MESSAGE).not.toMatch(DASHES);
    });
  });

  describe("fillTimeProblem", () => {
    it("passes a human-paced form", () => {
      expect(fillTimeProblem(String(NOW - MIN_FILL_MS), NOW)).toBeNull();
      expect(fillTimeProblem(String(NOW - 5 * 60_000), NOW)).toBeNull();
      expect(fillTimeProblem(String(NOW - DAY), NOW)).toBeNull();
    });

    it("flags a form sent faster than a person could", () => {
      expect(fillTimeProblem(String(NOW), NOW)).toBe("too_fast");
      expect(fillTimeProblem(String(NOW - MIN_FILL_MS + 1), NOW)).toBe("too_fast");
    });

    it("flags a missing or garbled timer", () => {
      for (const raw of [null, "", "abc", "1e12", "-5", "12.5", "0", "99999999999999999"]) {
        expect(fillTimeProblem(raw, NOW)).toBe("missing");
      }
      expect(fillTimeProblem(new File([], "x"), NOW)).toBe("missing");
    });

    it("flags a timer over a day old, or a day ahead", () => {
      expect(fillTimeProblem(String(NOW - DAY - 1), NOW)).toBe("stale");
      expect(fillTimeProblem(String(NOW + DAY + 1), NOW)).toBe("stale");
    });

    it("can't measure a clock that runs ahead, so lets it pass", () => {
      expect(fillTimeProblem(String(NOW + 60_000), NOW)).toBeNull();
    });
  });

  describe("honeypotFilled", () => {
    it("is true only when the trap holds something", () => {
      expect(honeypotFilled(null)).toBe(false);
      expect(honeypotFilled("")).toBe(false);
      expect(honeypotFilled(" ")).toBe(true);
      expect(honeypotFilled("https://spam.example")).toBe(true);
      expect(honeypotFilled(new File(["x"], "x.txt"))).toBe(true);
    });
  });

  describe("firstFieldErrors", () => {
    it("keeps the first message for each known field", () => {
      expect(
        firstFieldErrors([
          { path: ["email"], message: "first" },
          { path: ["email"], message: "second" },
          { path: ["name"], message: "name" },
          { path: [], message: "form level" },
          { path: ["company_site"], message: "not a field" },
          { path: [0], message: "numeric" },
        ]),
      ).toEqual({ email: "first", name: "name" });
    });
  });

  describe("readBookingValues", () => {
    it("reads every field as text, missing and file fields as empty", () => {
      const data = new FormData();
      data.set("name", "Ada");
      data.set("message", new File(["x"], "x.txt"));
      data.set("company_site", "trap");
      const values = readBookingValues(data);
      expect(values).toEqual({
        name: "Ada",
        email: "",
        company: "",
        website: "",
        xHandle: "",
        launching: "",
        launchDate: "",
        budget: "",
        message: "",
      });
    });

    it("caps very long values", () => {
      const data = new FormData();
      data.set("message", "a".repeat(10_000));
      expect(readBookingValues(data).message).toHaveLength(4000);
    });
  });

  describe("isCalendarDate", () => {
    it("accepts real dates, leap days included", () => {
      expect(isCalendarDate("2026-11-12")).toBe(true);
      expect(isCalendarDate("2028-02-29")).toBe(true);
      expect(isCalendarDate("2026-12-31")).toBe(true);
    });

    it("refuses dates that roll over or don't exist", () => {
      for (const value of ["2026-02-31", "2026-02-29", "2026-04-31", "2026-13-01", "2026-00-10", "0000-01-01", "2026-1-1", ""]) {
        expect(isCalendarDate(value)).toBe(false);
      }
    });
  });
});
