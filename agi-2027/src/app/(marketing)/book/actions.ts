"use server";

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
import { rateKey } from "@/lib/rate-limit";
import { clientIp } from "@/lib/request-ip";
import { siteConfig } from "@/lib/site";

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

  // A salted hash of the visitor's IP, so the rate limit table never holds a real address.
  const result = await submitLead(booking, { source, rateKey: rateKey(clientIp(await headers())) });
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
