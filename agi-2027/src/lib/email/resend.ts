import "server-only";

/*
 * A tiny Resend client: one POST to their REST API, no SDK.
 * https://resend.com/docs/api-reference/emails/send-email
 */

const RESEND_ENDPOINT = "https://api.resend.com/emails";

/** Resend's shared test sender. It only delivers to the Resend account's own address until a domain is verified. */
export const DEFAULT_EMAIL_FROM = "AGI 2027 <onboarding@resend.dev>";

const TIMEOUT_MS = 10_000;

export type EmailMessage = {
  to: string;
  subject: string;
  html: string;
  text: string;
  /** Where replies go, such as the lead's own address. */
  replyTo?: string;
  /** Defaults to EMAIL_FROM, then Resend's test sender. */
  from?: string;
  /** Resend drops a repeat send with the same key within 24 hours. Use the outbox row id. */
  idempotencyKey?: string;
};

export type SendEmailResult = { ok: true; id: string } | { ok: false; error: string; status?: number };

export function emailFrom(): string {
  return process.env.EMAIL_FROM?.trim() || DEFAULT_EMAIL_FROM;
}

/**
 * Sends one email. Never throws: a missing key, a timeout or an error from
 * Resend comes back as { ok: false } with a short reason for the outbox.
 */
export async function sendEmail(
  message: EmailMessage,
  { apiKey = process.env.RESEND_API_KEY, fetchImpl = fetch }: { apiKey?: string; fetchImpl?: typeof fetch } = {},
): Promise<SendEmailResult> {
  if (!apiKey) return { ok: false, error: "RESEND_API_KEY is not set, so no email was sent." };

  const headers: Record<string, string> = {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
  if (message.idempotencyKey) headers["Idempotency-Key"] = message.idempotencyKey;

  let response: Response;
  try {
    response = await fetchImpl(RESEND_ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify({
        from: message.from ?? emailFrom(),
        to: [message.to],
        subject: message.subject,
        html: message.html,
        text: message.text,
        ...(message.replyTo ? { reply_to: message.replyTo } : {}),
      }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store",
    });
  } catch (error) {
    const timedOut = error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError");
    return { ok: false, error: timedOut ? "Resend didn't answer within 10 seconds." : "Couldn't reach Resend." };
  }

  const body = (await response.json().catch(() => null)) as { id?: unknown; message?: unknown; name?: unknown } | null;
  if (!response.ok) {
    const detail = typeof body?.message === "string" ? body.message : response.statusText;
    return { ok: false, status: response.status, error: `Resend said ${response.status}: ${detail}`.slice(0, 500) };
  }
  if (typeof body?.id !== "string") {
    return { ok: false, status: response.status, error: "Resend accepted the email but returned no id." };
  }
  return { ok: true, id: body.id };
}
