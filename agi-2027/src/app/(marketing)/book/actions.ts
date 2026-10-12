"use server";

import { createHash } from "node:crypto";

import { headers } from "next/headers";
import { after } from "next/server";

import {
  bookingSchema,
  HONEYPOT_FIELD,
  LEAD_SOURCES,
  STARTED_AT_FIELD,
  type BookingState,
  type LeadSource,
} from "@/lib/leads/booking";
import {
  FIELDS_MESSAGE,
  FILL_TIME_MESSAGE,
  fillTimeProblem,
  firstFieldErrors,
  honeypotFilled,
  isCalendarDate,
  LAUNCH_DATE_MESSAGE,
  readBookingValues,
  submitErrorMessage,
} from "@/lib/leads/errors";
import { submitLead } from "@/lib/leads/submit";
import { deliverOutbox } from "@/lib/outbox/deliver";
import { siteConfig } from "@/lib/site";

/** Used only when RATE_LIMIT_SALT is missing, so local development still rate limits. */
const FALLBACK_SALT = "agi-2027-dev-rate-limit-salt";
let warnedAboutSalt = false;

/**
 * The "Book a campaign" form (the /book page and the home page's final call
 * to action). Spam checks first, then the schema, then one database call that
 * rate limits, saves the lead, queues the owner's email and logs it. The email
 * goes out after the response, so the form answers fast.
 */
export async function submitBooking(_prev: BookingState, formData: FormData): Promise<BookingState> {
  const values = readBookingValues(formData);

  // People never see the honeypot. A bot that fills it gets the same thank-you, and nothing is saved.
  if (honeypotFilled(formData.get(HONEYPOT_FIELD))) {
    return { status: "success", name: values.name.trim(), email: values.email.trim() };
  }

  if (fillTimeProblem(formData.get(STARTED_AT_FIELD), Date.now())) {
    return { status: "error", message: FILL_TIME_MESSAGE, values };
  }

  const parsed = bookingSchema.safeParse(values);
  if (!parsed.success) {
    return {
      status: "error",
      message: FIELDS_MESSAGE,
      fieldErrors: firstFieldErrors(parsed.error.issues),
      values,
    };
  }
  const booking = parsed.data;
  if (booking.launchDate && !isCalendarDate(booking.launchDate)) {
    return {
      status: "error",
      message: FIELDS_MESSAGE,
      fieldErrors: { launchDate: LAUNCH_DATE_MESSAGE },
      values,
    };
  }

  const rawSource = formData.get("source");
  const source: LeadSource = (LEAD_SOURCES as readonly unknown[]).includes(rawSource)
    ? (rawSource as LeadSource)
    : "book_page";

  const rateKey = hashIp(clientIp(await headers()));

  const result = await submitLead(booking, { source, rateKey });
  if (!result.ok) {
    return { status: "error", message: submitErrorMessage(result.reason, siteConfig.contactEmail), values };
  }

  // Send the owner's email once the response is out. If it fails, the outbox retries it.
  const outboxId = result.outboxId;
  after(async () => {
    try {
      await deliverOutbox({ id: outboxId, limit: 1 });
    } catch {
      console.error(`[book] delivery after submit failed for outbox ${outboxId}`);
    }
  });

  return { status: "success", name: booking.name, email: booking.email };
}

/**
 * The visitor's IP: the first x-forwarded-for entry, else x-real-ip. On
 * Vercel the platform sets these, so a visitor can't pick their own.
 */
function clientIp(list: Headers): string {
  const forwarded = list.get("x-forwarded-for")?.split(",")[0]?.trim();
  if (forwarded) return forwarded;
  const real = list.get("x-real-ip")?.trim();
  return real || "unknown";
}

/** A salted SHA-256 of the IP, so the rate limit table never holds a real address. */
function hashIp(ip: string): string {
  let salt = process.env.RATE_LIMIT_SALT;
  if (!salt) {
    if (!warnedAboutSalt) {
      warnedAboutSalt = true;
      console.warn("[book] RATE_LIMIT_SALT is not set. Using a built-in salt; set one before launch.");
    }
    salt = FALLBACK_SALT;
  }
  return createHash("sha256").update(salt + ip).digest("hex");
}
