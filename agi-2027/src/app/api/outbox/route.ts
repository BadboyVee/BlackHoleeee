import { createHash, timingSafeEqual } from "node:crypto";

import { deliverOutbox } from "@/lib/outbox/deliver";

/*
 * Drains the email outbox. A scheduler (Supabase Cron, or any cron service)
 * calls it with `Authorization: Bearer <CRON_SECRET>`.
 *
 * Always dynamic: with Cache Components the old `export const dynamic` config
 * is gone, and POST handlers are never prerendered or cached. Only POST is
 * exported, so Next.js answers every other method with 405.
 */

/** Seconds a run may take: up to 20 emails, five at a time, each with a 10 second timeout. */
export const maxDuration = 60;

const BATCH = 20;

const noStore = { "Cache-Control": "no-store" };

export async function POST(request: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret) {
    return Response.json({ error: "CRON_SECRET is not set." }, { status: 503, headers: noStore });
  }

  const given = request.headers.get("authorization") ?? "";
  if (!sameSecret(given, `Bearer ${secret}`)) {
    return Response.json(
      { error: "Unauthorized" },
      { status: 401, headers: { ...noStore, "WWW-Authenticate": "Bearer" } },
    );
  }

  const summary = await deliverOutbox({ limit: BATCH });
  return Response.json(summary, { status: summary.error ? 503 : 200, headers: noStore });
}

/** Constant-time comparison. Hashing first gives both sides the same length, so length leaks nothing. */
function sameSecret(given: string, expected: string): boolean {
  const a = createHash("sha256").update(given).digest();
  const b = createHash("sha256").update(expected).digest();
  return timingSafeEqual(a, b);
}
