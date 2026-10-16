import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LINK_EXPIRED, TOO_MANY_TRIES } from "@/lib/auth/messages";
import type { AuthFormState } from "@/lib/auth/schemas";

class Redirect extends Error {
  constructor(readonly url: string) {
    super(`redirect ${url}`);
  }
}

const mocks = vi.hoisted(() => ({
  headers: new Headers(),
  cookieJar: new Map<string, string>(),
  hitRateLimit: vi.fn<(kind: string, value: string) => Promise<boolean>>(async () => true),
  site: { name: "AGI 2027", url: "https://agi2027.example", contactEmail: "hi@agi2027.example" },
  claims: null as Record<string, unknown> | null,
  profile: null as { role: string; status: string } | null,
  auth: {
    signInWithPassword: vi.fn(),
    signUp: vi.fn(),
    signInWithOAuth: vi.fn(),
    resetPasswordForEmail: vi.fn(),
    resend: vi.fn(),
    updateUser: vi.fn(),
    signOut: vi.fn(),
    exchangeCodeForSession: vi.fn(),
    verifyOtp: vi.fn(),
  },
}));

vi.mock("server-only", () => ({}));
vi.mock("next/headers", () => ({
  headers: async () => mocks.headers,
  cookies: async () => ({
    getAll: () => [...mocks.cookieJar].map(([name, value]) => ({ name, value })),
    delete: (name: string) => mocks.cookieJar.delete(name),
  }),
}));
vi.mock("next/navigation", () => ({
  redirect: (url: string) => {
    throw new Redirect(url);
  },
}));
vi.mock("@/lib/rate-limit", () => ({ hitRateLimit: mocks.hitRateLimit }));
vi.mock("@/lib/site", () => ({ siteConfig: mocks.site }));
vi.mock("@/lib/supabase/server", () => ({
  createClient: async () => ({
    auth: { ...mocks.auth, getClaims: async () => ({ data: mocks.claims ? { claims: mocks.claims } : null, error: null }) },
    from: () => {
      const query = {
        select: () => query,
        eq: () => query,
        maybeSingle: async () => ({ data: mocks.profile, error: null }),
      };
      return query;
    },
  }),
}));

const actions = await import("@/app/(auth)/actions");
const { GET: callback } = await import("@/app/auth/callback/route");
const { GET: confirm } = await import("@/app/auth/confirm/route");

const idle: AuthFormState = { status: "idle" };
const ORIGIN = "https://deploy-preview-7--agi2027.netlify.app";
const USER = "8a7d5c1e-0000-4000-8000-000000000001";

function form(values: Record<string, string>) {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

/** Runs an action and says how it ended: with a state for the form, or a redirect. */
async function run<T>(promise: Promise<T>): Promise<{ state?: T; redirect?: string }> {
  try {
    return { state: await promise };
  } catch (error) {
    if (error instanceof Redirect) return { redirect: error.url };
    throw error;
  }
}

function signedIn(role?: string, profile?: { role: string; status: string }) {
  mocks.claims = { sub: USER, ...(role ? { user_role: role } : {}) };
  mocks.profile = profile ?? null;
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.co");
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x");
  mocks.headers = new Headers({ origin: ORIGIN, "x-forwarded-for": "203.0.113.7" });
  mocks.cookieJar = new Map();
  mocks.claims = null;
  mocks.profile = null;
  mocks.hitRateLimit.mockResolvedValue(true);
  mocks.auth.signInWithPassword.mockResolvedValue({ data: {}, error: null });
  mocks.auth.signUp.mockResolvedValue({ data: { session: null, user: { id: USER } }, error: null });
  mocks.auth.signInWithOAuth.mockResolvedValue({ data: { url: "https://project.supabase.co/auth/v1/authorize?provider=google" }, error: null });
  mocks.auth.resetPasswordForEmail.mockResolvedValue({ data: {}, error: null });
  mocks.auth.resend.mockResolvedValue({ data: {}, error: null });
  mocks.auth.updateUser.mockResolvedValue({ data: {}, error: null });
  mocks.auth.signOut.mockResolvedValue({ error: null });
  mocks.auth.exchangeCodeForSession.mockResolvedValue({ data: {}, error: null });
  mocks.auth.verifyOtp.mockResolvedValue({ data: {}, error: null });
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  for (const fn of Object.values(mocks.auth)) fn.mockReset();
  mocks.hitRateLimit.mockReset();
});

describe("signIn", () => {
  const good = { email: " Ada@Kled.ai ", password: "correct horse" };

  it("signs in, then goes where they were heading when their role may open it", async () => {
    signedIn("admin");
    const result = await run(actions.signIn(idle, form({ ...good, next: "/admin/review" })));
    expect(result.redirect).toBe("/admin/review");
    expect(mocks.auth.signInWithPassword).toHaveBeenCalledWith({ email: "ada@kled.ai", password: "correct horse" });
  });

  it("goes to the role's home otherwise, reading the role from the database when the token has none", async () => {
    signedIn(undefined, { role: "creator", status: "active" });
    expect((await run(actions.signIn(idle, form(good)))).redirect).toBe("/dashboard");
    expect((await run(actions.signIn(idle, form({ ...good, next: "https://evil.example" })))).redirect).toBe("/dashboard");
    signedIn(undefined, { role: "applicant", status: "active" });
    expect((await run(actions.signIn(idle, form({ ...good, next: "/admin" })))).redirect).toBe("/application");
  });

  it("rate limits by connection and by email address, before asking Supabase", async () => {
    signedIn("creator");
    await run(actions.signIn(idle, form(good)));
    expect(mocks.hitRateLimit).toHaveBeenCalledWith("sign_in_ip", "203.0.113.7");
    expect(mocks.hitRateLimit).toHaveBeenCalledWith("sign_in_email", "ada@kled.ai");

    mocks.hitRateLimit.mockReset();
    mocks.hitRateLimit.mockResolvedValueOnce(true).mockResolvedValueOnce(false);
    mocks.auth.signInWithPassword.mockClear();
    const { state } = await run(actions.signIn(idle, form(good)));
    expect(state).toEqual({ status: "error", message: TOO_MANY_TRIES, email: "ada@kled.ai" });
    expect(mocks.auth.signInWithPassword).not.toHaveBeenCalled();
  });

  it("explains a wrong password, keeps the email and never sends the password back", async () => {
    mocks.auth.signInWithPassword.mockResolvedValue({ data: {}, error: { code: "invalid_credentials", status: 400 } });
    const { state } = await run(actions.signIn(idle, form(good)));
    expect(state).toMatchObject({ status: "error", email: "ada@kled.ai" });
    expect(JSON.stringify(state)).not.toContain("correct horse");
  });

  it("offers to send the confirmation link again when the email isn't confirmed", async () => {
    mocks.auth.signInWithPassword.mockResolvedValue({ data: {}, error: { code: "email_not_confirmed", status: 400 } });
    const { state } = await run(actions.signIn(idle, form(good)));
    expect(state).toMatchObject({ status: "error", offer: "resend_confirmation" });
  });

  it("checks the fields first", async () => {
    const { state } = await run(actions.signIn(idle, form({ email: "ada", password: "" })));
    expect(state).toMatchObject({
      status: "error",
      fieldErrors: { email: "Enter your email address.", password: "Enter your password." },
      email: "ada",
    });
    expect(mocks.hitRateLimit).not.toHaveBeenCalled();
  });

  it("says accounts aren't connected when Supabase isn't set up, offering the contact email", async () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
    const { state } = await run(actions.signIn(idle, form(good)));
    expect(state).toMatchObject({ status: "error" });
    expect(state?.status === "error" && state.message).toContain("hi@agi2027.example");
  });
});

describe("signUp", () => {
  const good = { name: " Ada Lovelace ", email: "Ada@Kled.ai", password: "long enough" };

  it("creates the account with their name, and asks them to check their inbox", async () => {
    const { state } = await run(actions.signUp(idle, form({ ...good, next: "/dashboard/campaigns/x" })));
    expect(state).toEqual({ status: "sent", email: "ada@kled.ai" });
    expect(mocks.auth.signUp).toHaveBeenCalledWith({
      email: "ada@kled.ai",
      password: "long enough",
      options: {
        data: { full_name: "Ada Lovelace" },
        emailRedirectTo: `${ORIGIN}/auth/callback?flow=signup&next=%2Fdashboard%2Fcampaigns%2Fx`,
      },
    });
    expect(mocks.hitRateLimit).toHaveBeenCalledWith("sign_up_ip", "203.0.113.7");
  });

  it("goes straight in when the project doesn't ask for confirmation", async () => {
    mocks.auth.signUp.mockResolvedValue({ data: { session: { access_token: "t" }, user: { id: USER } }, error: null });
    signedIn("applicant");
    expect((await run(actions.signUp(idle, form(good)))).redirect).toBe("/application");
  });

  it("refuses a short password and a missing name", async () => {
    const { state } = await run(actions.signUp(idle, form({ name: "", email: "ada@kled.ai", password: "short" })));
    expect(state).toMatchObject({ fieldErrors: { name: "Tell us your name.", password: "Use at least 8 characters." } });
    expect(mocks.auth.signUp).not.toHaveBeenCalled();
  });

  it("stops at the rate limit", async () => {
    mocks.hitRateLimit.mockResolvedValue(false);
    expect((await run(actions.signUp(idle, form(good)))).state).toMatchObject({ message: TOO_MANY_TRIES });
    expect(mocks.auth.signUp).not.toHaveBeenCalled();
  });
});

describe("signInWithGoogle", () => {
  it("hands the browser to Google, coming back through the callback with where they were going", async () => {
    const result = await run(actions.signInWithGoogle(form({ next: "/dashboard/earnings" })));
    expect(result.redirect).toBe("https://project.supabase.co/auth/v1/authorize?provider=google");
    expect(mocks.auth.signInWithOAuth).toHaveBeenCalledWith({
      provider: "google",
      options: {
        redirectTo: `${ORIGIN}/auth/callback?flow=google&next=%2Fdashboard%2Fearnings`,
        queryParams: { prompt: "select_account" },
      },
    });
  });

  it("falls back to the host when there's no Origin header, and drops an unsafe next", async () => {
    mocks.headers = new Headers({ host: "agi2027.netlify.app", "x-forwarded-proto": "https" });
    await run(actions.signInWithGoogle(form({ next: "//evil.example" })));
    expect(mocks.auth.signInWithOAuth.mock.calls[0][0].options.redirectTo).toBe(
      "https://agi2027.netlify.app/auth/callback?flow=google",
    );
  });

  it("returns to sign in with a note when Google can't start", async () => {
    mocks.auth.signInWithOAuth.mockResolvedValue({ data: { url: null }, error: { code: "validation_failed" } });
    expect((await run(actions.signInWithGoogle(form({})))).redirect).toBe("/login?error=google");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
    expect((await run(actions.signInWithGoogle(form({})))).redirect).toBe("/login?error=google");
  });
});

describe("requestPasswordReset and resendConfirmation", () => {
  it("sends a reset link that comes back to the new password form", async () => {
    const { state } = await run(actions.requestPasswordReset(idle, form({ email: "Ada@Kled.ai" })));
    expect(state).toEqual({ status: "sent", email: "ada@kled.ai" });
    expect(mocks.auth.resetPasswordForEmail).toHaveBeenCalledWith("ada@kled.ai", {
      redirectTo: `${ORIGIN}/auth/callback?flow=recovery&next=%2Freset-password`,
    });
    expect(mocks.hitRateLimit).toHaveBeenCalledWith("auth_email_ip", "203.0.113.7");
    expect(mocks.hitRateLimit).toHaveBeenCalledWith("auth_email_address", "ada@kled.ai");
  });

  it("sends the confirmation link again", async () => {
    const { state } = await run(actions.resendConfirmation(idle, form({ email: "ada@kled.ai", next: "/dashboard" })));
    expect(state).toEqual({ status: "sent", email: "ada@kled.ai" });
    expect(mocks.auth.resend).toHaveBeenCalledWith({
      type: "signup",
      email: "ada@kled.ai",
      options: { emailRedirectTo: `${ORIGIN}/auth/callback?flow=signup&next=%2Fdashboard` },
    });
  });

  it("protects an inbox from being flooded", async () => {
    mocks.hitRateLimit.mockImplementation(async (kind) => kind !== "auth_email_address");
    expect((await run(actions.requestPasswordReset(idle, form({ email: "ada@kled.ai" })))).state).toMatchObject({
      message: TOO_MANY_TRIES,
    });
    expect(mocks.auth.resetPasswordForEmail).not.toHaveBeenCalled();
  });

  it("explains when Supabase can't send", async () => {
    mocks.auth.resetPasswordForEmail.mockResolvedValue({ data: {}, error: { code: "over_email_send_rate_limit" } });
    expect((await run(actions.requestPasswordReset(idle, form({ email: "ada@kled.ai" })))).state).toMatchObject({
      status: "error",
      message: TOO_MANY_TRIES,
    });
  });
});

describe("updatePassword", () => {
  const good = { password: "a new password", confirm: "a new password" };

  it("saves the new password and goes to the role's home", async () => {
    signedIn("creator");
    expect((await run(actions.updatePassword(idle, form(good)))).redirect).toBe("/dashboard");
    expect(mocks.auth.updateUser).toHaveBeenCalledWith({ password: "a new password" });
  });

  it("asks for a new link when the reset sign-in has gone", async () => {
    expect((await run(actions.updatePassword(idle, form(good)))).redirect).toBe("/forgot-password?status=expired");
    expect(mocks.auth.updateUser).not.toHaveBeenCalled();
  });

  it("checks both passwords match, and explains Supabase's refusals", async () => {
    signedIn("creator");
    expect((await run(actions.updatePassword(idle, form({ password: "a new password", confirm: "other" })))).state).toMatchObject({
      fieldErrors: { confirm: "The passwords don't match." },
    });
    mocks.auth.updateUser.mockResolvedValue({ data: {}, error: { code: "same_password" } });
    expect((await run(actions.updatePassword(idle, form(good)))).state).toMatchObject({ status: "error" });
  });
});

describe("signOut", () => {
  it("logs out on this device and says so on the sign-in page", async () => {
    expect((await run(actions.signOut())).redirect).toBe("/login?status=signed-out");
    expect(mocks.auth.signOut).toHaveBeenCalledWith({ scope: "local" });
  });

  it("comes back to a page on this site after signing in again, and only to one", async () => {
    const data = new FormData();
    data.set("next", "/invite/7c2e9a41d03f5b86");
    expect((await run(actions.signOut(data))).redirect).toBe(
      `/login?status=signed-out&next=${encodeURIComponent("/invite/7c2e9a41d03f5b86")}`,
    );
    data.set("next", "https://evil.example/x");
    expect((await run(actions.signOut(data))).redirect).toBe("/login?status=signed-out");
  });

  it("clears the session cookies by hand when Supabase can't be reached", async () => {
    mocks.auth.signOut.mockResolvedValue({ error: { code: "unexpected_failure" } });
    mocks.cookieJar = new Map([
      ["sb-project-auth-token.0", "a"],
      ["sb-project-auth-token.1", "b"],
      ["agi-look", "drop"],
    ]);
    expect((await run(actions.signOut())).redirect).toBe("/login?status=signed-out");
    expect([...mocks.cookieJar.keys()]).toEqual(["agi-look"]);
  });
});

describe("/auth/callback", () => {
  function get(query: string) {
    return callback(new NextRequest(new URL(`/auth/callback${query}`, ORIGIN)));
  }

  it("swaps the code for a session, then goes where they were heading, uncached", async () => {
    signedIn("admin");
    const response = await get("?code=abc&flow=google&next=%2Fadmin%2Freview");
    expect(mocks.auth.exchangeCodeForSession).toHaveBeenCalledWith("abc");
    expect(response.headers.get("location")).toBe(`${ORIGIN}/admin/review`);
    expect(response.headers.get("cache-control")).toContain("no-store");
  });

  it("sends a reset link to the new password form, and a new account to its home", async () => {
    signedIn("applicant");
    expect((await get("?code=abc&flow=recovery&next=%2Freset-password")).headers.get("location")).toBe(`${ORIGIN}/reset-password`);
    expect((await get("?code=abc&flow=signup&next=%2Fdashboard")).headers.get("location")).toBe(`${ORIGIN}/application`);
  });

  it("explains what to do when the swap fails, by kind of link", async () => {
    mocks.auth.exchangeCodeForSession.mockResolvedValue({ data: {}, error: { code: "bad_code_verifier" } });
    expect((await get("?code=abc&flow=signup")).headers.get("location")).toBe(`${ORIGIN}/login?status=confirmed`);
    expect((await get("?code=abc&flow=recovery")).headers.get("location")).toBe(`${ORIGIN}/forgot-password?status=expired`);
    expect((await get("?code=abc&flow=google")).headers.get("location")).toBe(`${ORIGIN}/login?error=google`);
  });

  it("treats an expired or reused link, or a cancelled Google sign in, as a failure without trying", async () => {
    expect((await get("?error=access_denied&error_code=otp_expired&flow=signup")).headers.get("location")).toBe(
      `${ORIGIN}/login?error=link`,
    );
    expect((await get("?error=access_denied&flow=google")).headers.get("location")).toBe(`${ORIGIN}/login?error=google`);
    expect((await get("?flow=google")).headers.get("location")).toBe(`${ORIGIN}/login?error=google`);
    expect(mocks.auth.exchangeCodeForSession).not.toHaveBeenCalled();
  });
});

describe("/auth/confirm", () => {
  function get(query: string) {
    return confirm(new NextRequest(new URL(`/auth/confirm${query}`, ORIGIN)));
  }

  it("checks the token hash, then lands on the role's home, or on the new password form for a reset", async () => {
    signedIn("applicant");
    const response = await get("?token_hash=h1&type=email");
    expect(mocks.auth.verifyOtp).toHaveBeenCalledWith({ type: "email", token_hash: "h1" });
    expect(response.headers.get("location")).toBe(`${ORIGIN}/application`);
    expect((await get("?token_hash=h2&type=recovery")).headers.get("location")).toBe(`${ORIGIN}/reset-password`);
  });

  it("follows next as a path or a full URL on this site, never elsewhere", async () => {
    signedIn("creator");
    expect((await get(`?token_hash=h&type=email&next=${encodeURIComponent(`${ORIGIN}/dashboard/earnings`)}`)).headers.get("location")).toBe(
      `${ORIGIN}/dashboard/earnings`,
    );
    expect((await get("?token_hash=h&type=email&next=https%3A%2F%2Fevil.example%2Fx")).headers.get("location")).toBe(
      `${ORIGIN}/dashboard`,
    );
  });

  it("refuses broken links and explains expired ones", async () => {
    expect((await get("?type=email")).headers.get("location")).toBe(`${ORIGIN}/login?error=link`);
    expect((await get("?token_hash=h&type=sms")).headers.get("location")).toBe(`${ORIGIN}/login?error=link`);
    mocks.auth.verifyOtp.mockResolvedValue({ data: {}, error: { code: "otp_expired" } });
    expect((await get("?token_hash=h&type=email")).headers.get("location")).toBe(`${ORIGIN}/login?error=link`);
    expect((await get("?token_hash=h&type=recovery")).headers.get("location")).toBe(`${ORIGIN}/forgot-password?status=expired`);
  });

  it("uses the same words as the sign-in page for an expired link", () => {
    expect(LINK_EXPIRED).toMatch(/expired or was already used/);
  });
});
