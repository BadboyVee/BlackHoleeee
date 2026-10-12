import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { escapeHtml, escapeMultiline, singleLine } from "@/lib/email/html";
import { leadReceivedEmail, type LeadEmailData } from "@/lib/email/lead-received";

const mocks = vi.hoisted(() => ({ createAdminClient: vi.fn() }));

// The Resend client and the outbox worker are server-only; tests run them in plain Node.
vi.mock("server-only", () => ({}));
vi.mock("@/lib/supabase/admin", () => ({ createAdminClient: mocks.createAdminClient }));

const { DEFAULT_EMAIL_FROM, sendEmail } = await import("@/lib/email/resend");
const { deliverOutbox } = await import("@/lib/outbox/deliver");
const { POST } = await import("@/app/api/outbox/route");

const SITE = { siteUrl: "https://agi2027.test" };

const fullLead: LeadEmailData = {
  id: "7f1c1d2e-0000-4000-8000-000000000001",
  name: "Ada Lovelace",
  email: "ada@kled.ai",
  company: "Kled",
  website: "https://kled.ai",
  x_handle: "kled_ai",
  launching: "An AI data marketplace.\nLaunching on X first.",
  launch_date: "2026-11-12",
  budget: "10k_25k",
  message: "We want ten creators in week one.",
  source: "home_cta",
  created_at: "2026-10-12T17:05:00Z",
};

const minimalLead: LeadEmailData = {
  ...fullLead,
  website: null,
  x_handle: null,
  launch_date: null,
  message: null,
  source: "book_page",
};

const DASHES = /[\u2013\u2014]/;

describe("html helpers", () => {
  it("escapes the five HTML characters", () => {
    expect(escapeHtml(`<a href="x" onclick='y'>&</a>`)).toBe(
      "&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;&lt;/a&gt;",
    );
  });

  it("keeps line breaks as <br> after escaping", () => {
    expect(escapeMultiline("one\r\ntwo\n<b>three</b>")).toBe("one<br>two<br>&lt;b&gt;three&lt;/b&gt;");
  });

  it("flattens text to one line", () => {
    expect(singleLine("  Kled\r\nBcc: someone\t\u0000 ")).toBe("Kled Bcc: someone");
  });
});

describe("leadReceivedEmail", () => {
  it("names the company in the subject", () => {
    expect(leadReceivedEmail(fullLead, SITE).subject).toBe("New campaign inquiry: Kled");
  });

  it("keeps the subject on one line", () => {
    const { subject } = leadReceivedEmail({ ...fullLead, company: "Kled\r\nBcc: victim@example.com" }, SITE);
    expect(subject).toBe("New campaign inquiry: Kled Bcc: victim@example.com");
    expect(subject).not.toMatch(/[\r\n]/);
  });

  it("includes every field in both versions", () => {
    const { html, text } = leadReceivedEmail(fullLead, SITE);
    for (const line of [
      "Name: Ada Lovelace",
      "Email: ada@kled.ai",
      "Company: Kled",
      "Website: https://kled.ai",
      "X: @kled_ai",
      "Launching: An AI data marketplace.\nLaunching on X first.",
      "Launch date: 12 Nov 2026",
      "Budget: $10k to $25k",
      "Message: We want ten creators in week one.",
      "Sent from: Home page form",
      "Received: 12 Oct 2026, 17:05 UTC",
    ]) {
      expect(text).toContain(line);
    }
    expect(html).toContain('href="mailto:ada@kled.ai"');
    expect(html).toContain('href="https://kled.ai"');
    expect(html).toContain('href="https://x.com/kled_ai"');
    expect(html).toContain("An AI data marketplace.<br>Launching on X first.");
    expect(html).toContain("12 Nov 2026");
    expect(html).toContain("$10k to $25k");
  });

  it("says where the full list will live", () => {
    const { html, text } = leadReceivedEmail(fullLead, SITE);
    expect(text).toContain("Every lead will also show in Admin > Leads once sign-in is live.");
    expect(text).toContain("https://agi2027.test/admin/leads");
    expect(html).toContain("Admin &gt; Leads");
    expect(html).toContain('href="https://agi2027.test/admin/leads"');
  });

  it("leaves out optional fields that are empty", () => {
    const { html, text } = leadReceivedEmail(minimalLead, SITE);
    for (const label of ["Website", "X:", "Launch date", "Message"]) {
      expect(text).not.toContain(label);
    }
    for (const label of [">Website<", ">X<", ">Launch date<", ">Message<"]) {
      expect(html).not.toContain(label);
    }
    expect(text).toContain("Sent from: Book a campaign page");
    expect(html).not.toContain("null");
    expect(text).not.toContain("null");
    expect(text).not.toContain("undefined");
  });

  it("escapes every value the visitor typed", () => {
    const evil: LeadEmailData = {
      ...fullLead,
      name: `<script>alert("name")</script>`,
      company: `Acme "Labs" & 'Co' <img src=x onerror=alert(1)>`,
      website: `https://kled.ai/?q="><script>alert(1)</script>`,
      launching: `<script>alert('launch')</script> and more text`,
      message: `"quoted" & 'single' </td></tr></table>`,
    };
    const { html, subject } = leadReceivedEmail(evil, SITE);
    expect(html).not.toContain("<script>");
    expect(html).not.toContain("<img");
    expect(html).not.toContain("</td></tr></table><");
    expect(html).toContain("&lt;script&gt;alert(&quot;name&quot;)&lt;/script&gt;");
    expect(html).toContain("Acme &quot;Labs&quot; &amp; &#39;Co&#39; &lt;img src=x onerror=alert(1)&gt;");
    expect(html).toContain('href="https://kled.ai/?q=&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"');
    expect(html).toContain("&lt;script&gt;alert(&#39;launch&#39;)&lt;/script&gt; and more text");
    expect(html).toContain("&quot;quoted&quot; &amp; &#39;single&#39; &lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;");
    // The subject is plain text (Resend sends it as a header), so it stays readable.
    expect(subject).toBe(`New campaign inquiry: Acme "Labs" & 'Co' <img src=x onerror=alert(1)>`);
  });

  it("only links websites and handles that are safe to link", () => {
    const { html } = leadReceivedEmail({ ...fullLead, website: "javascript:alert(1)", x_handle: "not a handle" }, SITE);
    expect(html).not.toContain('href="javascript:');
    expect(html).toContain("javascript:alert(1)");
    expect(html).not.toContain("https://x.com/not");
  });

  it("writes no em or en dashes", () => {
    for (const lead of [fullLead, minimalLead]) {
      const { html, text, subject } = leadReceivedEmail(lead, SITE);
      expect(html).not.toMatch(DASHES);
      expect(text).not.toMatch(DASHES);
      expect(subject).not.toMatch(DASHES);
    }
  });
});

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("sendEmail", () => {
  const message = {
    to: "owner@agi2027.test",
    subject: "New campaign inquiry: Kled",
    html: "<p>Hi</p>",
    text: "Hi",
    replyTo: "ada@kled.ai",
    idempotencyKey: "outbox-1",
  };

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("does nothing without an API key", async () => {
    const fetchImpl = vi.fn();
    const result = await sendEmail(message, { apiKey: "", fetchImpl });
    expect(result).toEqual({ ok: false, error: "RESEND_API_KEY is not set, so no email was sent." });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("posts the email to Resend", async () => {
    vi.stubEnv("EMAIL_FROM", "");
    const fetchImpl = vi.fn(async () => jsonResponse(200, { id: "email_123" }));
    const result = await sendEmail(message, { apiKey: "re_test", fetchImpl });
    expect(result).toEqual({ ok: true, id: "email_123" });

    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("https://api.resend.com/emails");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({
      Authorization: "Bearer re_test",
      "Content-Type": "application/json",
      "Idempotency-Key": "outbox-1",
    });
    expect(JSON.parse(init.body as string)).toEqual({
      from: DEFAULT_EMAIL_FROM,
      to: ["owner@agi2027.test"],
      subject: "New campaign inquiry: Kled",
      html: "<p>Hi</p>",
      text: "Hi",
      reply_to: "ada@kled.ai",
    });
  });

  it("uses EMAIL_FROM when it's set", async () => {
    vi.stubEnv("EMAIL_FROM", "AGI 2027 <hello@agi2027.test>");
    const fetchImpl = vi.fn(async () => jsonResponse(200, { id: "email_123" }));
    await sendEmail(message, { apiKey: "re_test", fetchImpl });
    const [, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(init.body as string).from).toBe("AGI 2027 <hello@agi2027.test>");
  });

  it("reports Resend's error", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(403, { statusCode: 403, name: "validation_error", message: "Domain not verified." }),
    );
    const result = await sendEmail(message, { apiKey: "re_test", fetchImpl });
    expect(result).toEqual({ ok: false, status: 403, error: "Resend said 403: Domain not verified." });
  });

  it("reports a network failure without throwing", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new TypeError("fetch failed");
    });
    const result = await sendEmail(message, { apiKey: "re_test", fetchImpl });
    expect(result).toEqual({ ok: false, error: "Couldn't reach Resend." });
  });

  it("reports a timeout", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new DOMException("The operation timed out.", "TimeoutError");
    });
    const result = await sendEmail(message, { apiKey: "re_test", fetchImpl });
    expect(result).toEqual({ ok: false, error: "Resend didn't answer within 10 seconds." });
  });
});

type OutboxRowFixture = {
  id: string;
  channel: string;
  recipient: string;
  template: string;
  payload: Record<string, unknown>;
  attempts: number;
};

const leadRow: OutboxRowFixture = {
  id: "0b0b0b0b-0000-4000-8000-000000000001",
  channel: "email",
  recipient: "owner",
  template: "lead_received",
  payload: { lead_id: fullLead.id },
  attempts: 1,
};

/** A stand-in for the service client: claim_outbox hands out `rows`, and leads.select finds `lead`. */
function fakeAdmin({
  rows = [leadRow],
  lead = fullLead as LeadEmailData | null,
  claimError = null as { code: string; message: string } | null,
} = {}) {
  const rpc = vi.fn(async (fn: string, args: Record<string, unknown>) => {
    void args;
    if (fn === "claim_outbox") return { data: claimError ? null : rows, error: claimError };
    return { data: null, error: null };
  });
  const eq = vi.fn(() => ({ maybeSingle: async () => ({ data: lead, error: null }) }));
  const from = vi.fn(() => ({ select: () => ({ eq }) }));
  return { rpc, from, eq };
}

function finishCalls(admin: ReturnType<typeof fakeAdmin>) {
  return admin.rpc.mock.calls.filter(([fn]) => fn === "finish_outbox").map(([, args]) => args);
}

describe("deliverOutbox", () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  let logs: string[];

  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.test");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    vi.stubEnv("SUPABASE_SECRET_KEY", "sb_secret_test");
    vi.stubEnv("RESEND_API_KEY", "re_test");
    vi.stubEnv("LEADS_NOTIFY_EMAIL", "owner@agi2027.test");
    vi.stubEnv("EMAIL_FROM", "");
    fetchMock = vi.fn(async () => jsonResponse(200, { id: "email_123" }));
    vi.stubGlobal("fetch", fetchMock);
    logs = [];
    for (const level of ["log", "info", "warn", "error"] as const) {
      vi.spyOn(console, level).mockImplementation((...args: unknown[]) => {
        logs.push(args.map(String).join(" "));
      });
    }
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    mocks.createAdminClient.mockReset();
  });

  it("sends the lead email to the owner with replies going to the lead", async () => {
    const admin = fakeAdmin();
    mocks.createAdminClient.mockReturnValue(admin);

    const summary = await deliverOutbox({ id: leadRow.id, limit: 1 });

    expect(summary).toEqual({ claimed: 1, sent: 1, failed: 0 });
    expect(admin.rpc).toHaveBeenCalledWith("claim_outbox", { p_limit: 1, p_id: leadRow.id });
    expect(admin.from).toHaveBeenCalledWith("leads");
    expect(admin.eq).toHaveBeenCalledWith("id", fullLead.id);

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.to).toEqual(["owner@agi2027.test"]);
    expect(body.reply_to).toBe("ada@kled.ai");
    expect(body.subject).toBe("New campaign inquiry: Kled");
    expect(body.from).toBe(DEFAULT_EMAIL_FROM);
    expect(body.text).toContain("Budget: $10k to $25k");
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe(`outbox-${leadRow.id}`);

    expect(finishCalls(admin)).toEqual([{ p_id: leadRow.id, p_ok: true, p_error: null }]);
  });

  it("claims all due rows when no id is given", async () => {
    const admin = fakeAdmin({ rows: [] });
    mocks.createAdminClient.mockReturnValue(admin);
    expect(await deliverOutbox({ limit: 20 })).toEqual({ claimed: 0, sent: 0, failed: 0 });
    expect(admin.rpc).toHaveBeenCalledWith("claim_outbox", { p_limit: 20, p_id: null });
  });

  it("fails the row with a clear error when RESEND_API_KEY is missing", async () => {
    vi.stubEnv("RESEND_API_KEY", "");
    const admin = fakeAdmin();
    mocks.createAdminClient.mockReturnValue(admin);

    expect(await deliverOutbox()).toEqual({ claimed: 1, sent: 0, failed: 1 });
    expect(fetchMock).not.toHaveBeenCalled();
    const [finish] = finishCalls(admin);
    expect(finish).toMatchObject({ p_id: leadRow.id, p_ok: false });
    expect(finish.p_error).toContain("RESEND_API_KEY is not set");
  });

  it("fails the row with a clear error when LEADS_NOTIFY_EMAIL is missing", async () => {
    vi.stubEnv("LEADS_NOTIFY_EMAIL", "");
    const admin = fakeAdmin();
    mocks.createAdminClient.mockReturnValue(admin);

    expect(await deliverOutbox()).toEqual({ claimed: 1, sent: 0, failed: 1 });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(finishCalls(admin)[0].p_error).toContain("LEADS_NOTIFY_EMAIL is not set");
  });

  it("records Resend's error so the outbox can retry", async () => {
    fetchMock.mockImplementation(async () => jsonResponse(500, { message: "Internal error" }));
    const admin = fakeAdmin();
    mocks.createAdminClient.mockReturnValue(admin);

    expect(await deliverOutbox()).toEqual({ claimed: 1, sent: 0, failed: 1 });
    expect(finishCalls(admin)).toEqual([{ p_id: leadRow.id, p_ok: false, p_error: "Resend said 500: Internal error" }]);
  });

  it("fails rows whose lead is gone, or whose template or channel is unknown", async () => {
    const admin = fakeAdmin({
      lead: null,
      rows: [
        leadRow,
        { ...leadRow, id: "row-2", template: "mystery" },
        { ...leadRow, id: "row-3", channel: "telegram" },
        { ...leadRow, id: "row-4", payload: {} },
      ],
    });
    mocks.createAdminClient.mockReturnValue(admin);

    expect(await deliverOutbox()).toEqual({ claimed: 4, sent: 0, failed: 4 });
    // Rows go out in parallel, so they can finish in any order.
    const errors = Object.fromEntries(finishCalls(admin).map((call) => [call.p_id, call.p_error]));
    expect(errors).toEqual({
      [leadRow.id]: "The lead no longer exists.",
      "row-2": 'Unknown template "mystery".',
      "row-3": 'Channel "telegram" isn\'t supported yet.',
      "row-4": "The payload has no lead_id.",
    });
  });

  it("sends to a plain address recipient", async () => {
    const admin = fakeAdmin({ rows: [{ ...leadRow, recipient: "someone@agi2027.test" }] });
    mocks.createAdminClient.mockReturnValue(admin);
    await deliverOutbox();
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(init.body as string).to).toEqual(["someone@agi2027.test"]);
  });

  it("returns an error instead of throwing when Supabase isn't configured", async () => {
    vi.stubEnv("SUPABASE_SECRET_KEY", "");
    const summary = await deliverOutbox();
    expect(summary).toMatchObject({ claimed: 0, sent: 0, failed: 0 });
    expect(summary.error).toMatch(/isn't configured/);
    expect(mocks.createAdminClient).not.toHaveBeenCalled();
  });

  it("returns an error instead of throwing when claiming fails", async () => {
    mocks.createAdminClient.mockReturnValue(fakeAdmin({ claimError: { code: "42501", message: "permission denied" } }));
    const summary = await deliverOutbox();
    expect(summary).toEqual({ claimed: 0, sent: 0, failed: 0, error: "Couldn't claim outbox rows." });
  });

  it("never logs names or email addresses", async () => {
    fetchMock.mockImplementation(async () =>
      jsonResponse(422, { message: "Invalid `to` field: owner@agi2027.test" }),
    );
    mocks.createAdminClient.mockReturnValue(fakeAdmin());
    await deliverOutbox();
    expect(logs.length).toBeGreaterThan(0);
    const output = logs.join("\n");
    for (const secret of ["ada@kled.ai", "Ada Lovelace", "owner@agi2027.test", "Kled"]) {
      expect(output).not.toContain(secret);
    }
  });
});

describe("POST /api/outbox", () => {
  function call(authorization?: string) {
    return POST(
      new Request("http://localhost/api/outbox", {
        method: "POST",
        headers: authorization ? { Authorization: authorization } : {},
      }),
    );
  }

  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.test");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    vi.stubEnv("SUPABASE_SECRET_KEY", "sb_secret_test");
    vi.stubEnv("CRON_SECRET", "s3cret-value");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    mocks.createAdminClient.mockReset();
  });

  it("is unavailable until CRON_SECRET is set", async () => {
    vi.stubEnv("CRON_SECRET", "");
    const response = await call("Bearer anything");
    expect(response.status).toBe(503);
    expect(mocks.createAdminClient).not.toHaveBeenCalled();
  });

  it("refuses a missing or wrong secret", async () => {
    for (const header of [undefined, "Bearer wrong", "s3cret-value", "Bearer s3cret-valu", "bearer s3cret-value"]) {
      const response = await call(header);
      expect(response.status).toBe(401);
      expect(response.headers.get("WWW-Authenticate")).toBe("Bearer");
    }
    expect(mocks.createAdminClient).not.toHaveBeenCalled();
  });

  it("drains up to 20 rows and returns the counts", async () => {
    const admin = fakeAdmin({ rows: [] });
    mocks.createAdminClient.mockReturnValue(admin);
    const response = await call("Bearer s3cret-value");
    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(await response.json()).toEqual({ claimed: 0, sent: 0, failed: 0 });
    expect(admin.rpc).toHaveBeenCalledWith("claim_outbox", { p_limit: 20, p_id: null });
  });

  it("answers 503 when the outbox can't be read", async () => {
    vi.stubEnv("SUPABASE_SECRET_KEY", "");
    const response = await call("Bearer s3cret-value");
    expect(response.status).toBe(503);
    expect(await response.json()).toMatchObject({ claimed: 0, error: expect.stringContaining("isn't configured") });
  });
});
