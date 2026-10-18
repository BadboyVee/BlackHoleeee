import "server-only";

import { after } from "next/server";

import { deliverOutbox } from "./deliver";

/**
 * Sends one queued email once the response is out, so the form answers
 * fast. If it fails, the row stays in the outbox for POST /api/outbox to
 * retry. Does nothing without a row (an account with no usable address).
 */
export function deliverSoon(outboxId: unknown, tag: string): void {
  if (typeof outboxId !== "string" || !outboxId) return;
  after(async () => {
    try {
      await deliverOutbox({ id: outboxId, limit: 1 });
    } catch {
      console.error(`[${tag}] delivery failed for outbox ${outboxId}`);
    }
  });
}
