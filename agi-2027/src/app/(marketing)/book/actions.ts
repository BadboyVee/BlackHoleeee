"use server";

import { createHash, createHmac } from "node:crypto";

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
  fillTimeMessage,
  fillTimeProblem,
  firstFieldErrors,
  honeypotFilled,
  readBookingValues,
  submitErrorMessage,
} from "@/lib/leads/errors";
import { submitLead } from "@/lib/leads/submit";
import { deliverOutbox } from "@/lib/outbox/deliver";
import { clientIp } from "@/lib/request-ip";
import { siteConfig } from "@/lib/site";

/** Used only when RATE_LIMIT_SALT and SUPABASE_SECRET_KEY are both missing, so local development still rate limits. */
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
    // No names or addresses, just enough to notice in the host's logs if real people ever trip it.
    console.warn("[book] The honeypot was filled, so nothing was saved.");
    return { status: "success", name: values.name.trim(), email: values.email.trim() };
  }

  if (fillTimeProblem(formData.get(STARTED_AT_FIELD), Date.now())) {
    return { status: "error", message: fillTimeMessage(siteConfig.contactEmail), values };
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

/** A salted SHA-256 of the IP, so the rate limit table never holds a real address. */
function hashIp(ip: string): string {
  return createHash("sha256").update(rateLimitSalt() + ip).digest("hex");
}

/**
 * RATE_LIMIT_SALT when it's set. Otherwise a value made from the Supabase
 * secret key, which the site needs to save a booking at all, so the salt is
 * still secret, as the privacy page says. The key itself never goes into the
 * hash. The built-in salt is only for local development without either.
 */
function rateLimitSalt(): string {
  const salt = process.env.RATE_LIMIT_SALT;
  if (salt) return salt;
  const secretKey = process.env.SUPABASE_SECRET_KEY;
  if (secretKey) return createHmac("sha256", secretKey).update("agi-2027 rate limit salt").digest("hex");
  if (!warnedAboutSalt) {
    warnedAboutSalt = true;
    console.warn("[book] Neither RATE_LIMIT_SALT nor SUPABASE_SECRET_KEY is set. Using the built-in development salt.");
  }
  return FALLBACK_SALT;
}
