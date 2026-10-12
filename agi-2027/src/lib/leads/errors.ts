import type { BookingFormValues } from "./booking";
import { MIN_FILL_MS } from "./booking";

/*
 * Pure helpers for the "Book a campaign" server action: the spam timer, the
 * field errors and the messages people see when something goes wrong. No
 * Next.js or Supabase imports, so they're easy to unit test.
 */

/** The form fields the action reads, in the order the form shows them. */
export const BOOKING_FIELDS = [
  "name",
  "email",
  "company",
  "website",
  "xHandle",
  "launching",
  "launchDate",
  "budget",
  "message",
] as const satisfies readonly (keyof BookingFormValues)[];

export type BookingField = (typeof BOOKING_FIELDS)[number];
export type BookingValues = Partial<Record<BookingField, string>>;

const DAY_MS = 24 * 60 * 60 * 1000;

/** Longest text we echo back to the form after an error. The schema rejects anything longer anyway. */
const MAX_ECHO = 4000;

/**
 * The raw text of every booking field, missing ones as "". Empty strings let
 * the schema give its friendly "Tell us your name." instead of a type error.
 */
export function readBookingValues(formData: FormData): Record<BookingField, string> {
  const values = {} as Record<BookingField, string>;
  for (const field of BOOKING_FIELDS) {
    const value = formData.get(field);
    values[field] = typeof value === "string" ? value.slice(0, MAX_ECHO) : "";
  }
  return values;
}

/** True when the hidden honeypot field has anything in it. People never see it, so only bots fill it. */
export function honeypotFilled(value: FormDataEntryValue | null): boolean {
  if (value === null) return false;
  return typeof value === "string" ? value.length > 0 : true;
}

export type FillTimeProblem = "missing" | "too_fast" | "stale";

/**
 * Checks the timestamp the form stamped when it appeared (milliseconds since
 * the epoch, from the browser's clock). Returns null when it looks human.
 *
 * A time in the future means the visitor's clock runs ahead of ours, so the
 * fill time can't be measured: that passes, since a bot could fake a past
 * time just as easily. The honeypot and the rate limit still apply.
 */
export function fillTimeProblem(raw: FormDataEntryValue | null, now: number): FillTimeProblem | null {
  if (typeof raw !== "string" || !/^\d{1,16}$/.test(raw.trim())) return "missing";
  const startedAt = Number(raw.trim());
  if (!Number.isSafeInteger(startedAt) || startedAt <= 0) return "missing";
  const elapsed = now - startedAt;
  if (elapsed > DAY_MS || elapsed < -DAY_MS) return "stale";
  if (elapsed >= 0 && elapsed < MIN_FILL_MS) return "too_fast";
  return null;
}

export const LAUNCH_DATE_MESSAGE = "Pick a date, or leave it empty.";

/**
 * True for a YYYY-MM-DD date that exists on the calendar. JavaScript reads
 * "2026-02-31" as 3 March, but Postgres refuses it, so the action checks
 * before saving rather than failing with a vague error.
 */
export function isCalendarDate(value: string): boolean {
  // Postgres has no year 0, and a rolled-over date no longer reads the same.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith("0000")) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

/** First message for each field, keyed by field name, from zod's issues. */
export function firstFieldErrors(
  issues: readonly { path: readonly PropertyKey[]; message: string }[],
): Partial<Record<BookingField, string>> {
  const errors: Partial<Record<BookingField, string>> = {};
  for (const issue of issues) {
    const field = issue.path[0];
    if (typeof field !== "string" || !(BOOKING_FIELDS as readonly string[]).includes(field)) continue;
    const key = field as BookingField;
    if (!errors[key]) errors[key] = issue.message;
  }
  return errors;
}

/** Why saving a lead failed, as far as the person filling the form needs to know. */
export type SubmitFailure = "rate_limited" | "not_configured" | "failed";

export type SubmitLeadResult =
  | { ok: true; leadId: string; outboxId: string }
  | { ok: false; reason: SubmitFailure; code?: string };

/** The errcode public.submit_lead raises when a connection sends too many bookings. */
export const RATE_LIMITED_CODE = "P0429";

/** Sorts a database error from submit_lead. PostgREST passes the Postgres errcode through as `code`. */
export function classifySubmitError(error: unknown): Exclude<SubmitFailure, "not_configured"> {
  if (error && typeof error === "object") {
    const { code, message } = error as { code?: unknown; message?: unknown };
    if (code === RATE_LIMITED_CODE) return "rate_limited";
    if (typeof message === "string" && message.trim() === "rate_limited") return "rate_limited";
  }
  return "failed";
}

export const FIELDS_MESSAGE = "Check the highlighted fields.";

export const FILL_TIME_MESSAGE =
  "Something about that send looked off. Check the form and send it again.";

/** The message for the whole form when saving fails. Adds the contact email when there is one. */
export function submitErrorMessage(reason: SubmitFailure, contactEmail: string): string {
  const email = contactEmail.trim();
  switch (reason) {
    case "rate_limited":
      return email
        ? `Too many requests from this connection. Try again in an hour, or email us at ${email}.`
        : "Too many requests from this connection. Try again in an hour, or email us.";
    case "not_configured":
      return email
        ? `Bookings aren't connected yet, so we couldn't save this. Email us at ${email} and we'll reply.`
        : "Bookings aren't connected yet, so we couldn't save this. Please try again soon.";
    case "failed":
      return email
        ? `We couldn't save that just now. Try again in a minute, or email us at ${email}.`
        : "We couldn't save that just now. Try again in a minute.";
  }
}
