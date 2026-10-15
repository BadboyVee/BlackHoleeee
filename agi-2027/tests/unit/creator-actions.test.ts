import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { inviteStateFromError, inviteStateMessage } from "@/lib/creators/messages";
import type { CreatorFormState } from "@/lib/creators/schemas";

class Redirect extends Error {
  constructor(readonly url: string) {
    super(`redirect ${url}`);
  }
}

const mocks = vi.hoisted(() => ({
  rpc: vi.fn(),
  update: vi.fn(),
  eq: vi.fn(),
  claims: { sub: "8a7d5c1e-0000-4000-8000-000000000001" } as Record<string, unknown> | null,
  refresh: vi.fn(),
  after: vi.fn(),
  deliverOutbox: vi.fn(),
  remove: vi.fn<(paths: string[]) => Promise<{ data: unknown[]; error: { message: string } | null }>>(async () => ({ data: [], error: null })),
}));

vi.mock("server-only", () => ({}));
vi.mock("next/cache", () => ({ refresh: mocks.refresh }));
vi.mock("next/server", () => ({ after: mocks.after }));
vi.mock("next/navigation", () => ({
  redirect: (url: string) => {
    throw new Redirect(url);
  },
}));
vi.mock("@/lib/outbox/deliver", () => ({ deliverOutbox: mocks.deliverOutbox }));
vi.mock("@/lib/supabase/server", () => ({
  createClient: async () => ({
    rpc: mocks.rpc,
    auth: { getClaims: async () => ({ data: mocks.claims ? { claims: mocks.claims } : null, error: null }) },
    storage: {
      from: (bucket: string) => {
        expect(bucket).toBe("avatars");
        return { remove: mocks.remove };
      },
    },
    from: (table: string) => {
      expect(table).toBe("profiles");
      return {
        update: (values: unknown) => {
          mocks.update(values);
          return { eq: async (column: string, value: unknown) => mocks.eq(column, value) };
        },
      };
    },
  }),
}));

const { redeemInvite, submitApplication } = await import("@/app/(auth)/application/actions");
const { reviewApplication } = await import("@/app/admin/applications/actions");
const { createInvite, revokeInvite } = await import("@/app/admin/invites/actions");
const { saveAvatar, savePayoutDetails, updateProfile } = await import("@/app/dashboard/profile/actions");

const idle: CreatorFormState = { status: "idle" };
const APPLICATION_ID = "2b0f6c1e-1111-4111-8111-111111111111";
const OUTBOX_ID = "3c1f7d2e-2222-4222-8222-222222222222";
const INVITE = "3f9a1c2b7d4e8f01";
const EVM = "0x52908400098527886E0F7030069857D2E4169EE7";

function form(values: Record<string, string | string[]>) {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    for (const item of Array.isArray(value) ? value : [value]) data.append(key, item);
  }
  return data;
}

async function run<T>(promise: Promise<T>): Promise<{ state?: T; redirect?: string }> {
  try {
    return { state: await promise };
  } catch (error) {
    if (error instanceof Redirect) return { redirect: error.url };
    throw error;
  }
}

const application = {
  displayName: "Amara Okafor",
  xHandle: "@amarabuilds",
  tiktok: "",
  youtube: "youtube.com/@amara",
  instagram: "",
  linkedin: "",
  niches: ["ai", "startups"],
  followers: "18.4k",
  avgViews: "6200",
  country: "NG",
  "bestPosts.0": "x.com/a/status/1",
  "bestPosts.1": "x.com/a/status/2",
  "bestPosts.2": "x.com/a/status/3",
  why: "I review AI tools every week for founders.",
  referralCode: "9F3A1C2B",
};

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.co");
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x");
  mocks.claims = { sub: "8a7d5c1e-0000-4000-8000-000000000001" };
  mocks.rpc.mockResolvedValue({ data: null, error: null });
  mocks.eq.mockResolvedValue({ error: null });
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  for (const fn of [mocks.rpc, mocks.update, mocks.eq, mocks.refresh, mocks.after, mocks.deliverOutbox]) fn.mockReset();
});

describe("submitApplication", () => {
  it("sends the cleaned answers to submit_application, emails the owner after the response and refreshes", async () => {
    mocks.rpc.mockResolvedValue({ data: [{ application_id: APPLICATION_ID, outbox_id: OUTBOX_ID }], error: null });
    const { state } = await run(submitApplication(idle, form(application)));
    expect(state).toEqual({ status: "saved" });
    expect(mocks.rpc).toHaveBeenCalledWith("submit_application", {
      p_display_name: "Amara Okafor",
      p_x_handle: "amarabuilds",
      p_tiktok_url: null,
      p_youtube_url: "https://youtube.com/@amara",
      p_instagram_url: null,
      p_linkedin_url: null,
      p_niches: ["ai", "startups"],
      p_followers: 18400,
      p_avg_views: 6200,
      p_country: "NG",
      p_best_posts: ["https://x.com/a/status/1", "https://x.com/a/status/2", "https://x.com/a/status/3"],
      p_why: "I review AI tools every week for founders.",
      p_referral_code: "9f3a1c2b",
    });
    expect(mocks.refresh).toHaveBeenCalled();
    expect(mocks.after).toHaveBeenCalledTimes(1);
    await mocks.after.mock.calls[0][0]();
    expect(mocks.deliverOutbox).toHaveBeenCalledWith({ id: OUTBOX_ID, limit: 1 });
  });

  it("puts each problem on its own field, the second post link included", async () => {
    const { state } = await run(submitApplication(idle, form({ ...application, "bestPosts.1": "", niches: [] })));
    expect(state).toMatchObject({
      status: "error",
      fieldErrors: { "bestPosts.1": "Paste a link to the post.", niches: "Pick at least one." },
    });
    expect(mocks.rpc).not.toHaveBeenCalled();
  });

  it("explains a handle someone else has, on the handle field", async () => {
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "23505", message: "duplicate key" } });
    const { state } = await run(submitApplication(idle, form(application)));
    expect(state).toMatchObject({ status: "error", fieldErrors: { xHandle: expect.stringContaining("already on another account") } });
  });

  it("refreshes to the status page when they already applied", async () => {
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "P0409", message: "already_applied" } });
    const { state } = await run(submitApplication(idle, form(application)));
    expect(state).toMatchObject({ status: "error", message: "You've already applied. We'll email you when there's news." });
    expect(mocks.refresh).toHaveBeenCalled();
  });

  it("says when accounts aren't connected", async () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
    expect((await run(submitApplication(idle, form(application)))).state).toMatchObject({ status: "error" });
    expect(mocks.rpc).not.toHaveBeenCalled();
  });
});

describe("redeemInvite", () => {
  it("approves them and goes to the creator app, sending the welcome after the response", async () => {
    mocks.rpc.mockResolvedValue({ data: OUTBOX_ID, error: null });
    const result = await run(redeemInvite(idle, form({ code: INVITE.toUpperCase() })));
    expect(result.redirect).toBe("/dashboard");
    expect(mocks.rpc).toHaveBeenCalledWith("redeem_invite", { p_code: INVITE });
    expect(mocks.after).toHaveBeenCalledTimes(1);
  });

  it("sends signed-out people to sign in first, back to the invite", async () => {
    mocks.claims = null;
    expect((await run(redeemInvite(idle, form({ code: INVITE })))).redirect).toBe(`/login?next=${encodeURIComponent(`/invite/${INVITE}`)}`);
  });

  it("explains a link that can't be used", async () => {
    for (const state of ["expired", "used_up", "revoked", "unknown"] as const) {
      mocks.rpc.mockResolvedValueOnce({ data: null, error: { code: "P0410", message: `invite_${state}` } });
      expect((await run(redeemInvite(idle, form({ code: INVITE })))).state, state).toEqual({
        status: "error",
        message: inviteStateMessage(state),
      });
    }
    expect((await run(redeemInvite(idle, form({ code: "short" })))).state).toEqual({ status: "error", message: inviteStateMessage("unknown") });
  });

  it("tells someone already in to head to the dashboard", async () => {
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "42501", message: "Only applicants can use an invite" } });
    expect((await run(redeemInvite(idle, form({ code: INVITE })))).state).toMatchObject({ message: expect.stringContaining("already in") });
  });
});

describe("reviewApplication", () => {
  it("approves with a note, emails the applicant after the response and refreshes", async () => {
    mocks.rpc.mockResolvedValue({ data: OUTBOX_ID, error: null });
    const { state } = await run(reviewApplication(idle, form({ id: APPLICATION_ID, decision: "approve", note: " Strong audience. " })));
    expect(state).toEqual({ status: "saved", message: "Approved. They'll get a welcome email." });
    expect(mocks.rpc).toHaveBeenCalledWith("review_application", {
      p_application: APPLICATION_ID,
      p_decision: "approve",
      p_note: "Strong audience.",
    });
    expect(mocks.after).toHaveBeenCalledTimes(1);
    expect(mocks.refresh).toHaveBeenCalled();
  });

  it("refuses a made-up decision or id, and explains a race", async () => {
    expect((await run(reviewApplication(idle, form({ id: APPLICATION_ID, decision: "maybe", note: "" })))).state).toMatchObject({ status: "error" });
    expect((await run(reviewApplication(idle, form({ id: "nope", decision: "approve", note: "" })))).state).toMatchObject({ status: "error" });
    expect(mocks.rpc).not.toHaveBeenCalled();
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "P0409", message: "already_reviewed" } });
    expect((await run(reviewApplication(idle, form({ id: APPLICATION_ID, decision: "reject", note: "" })))).state).toMatchObject({
      message: expect.stringContaining("already decided"),
    });
  });
});

describe("invites", () => {
  it("creates a link with an optional limit and an expiry worked out from now", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-13T12:00:00Z"));
    const { state } = await run(createInvite(idle, form({ label: " Telegram ", maxUses: "25", expiresIn: "7d" })));
    vi.useRealTimers();
    expect(state).toMatchObject({ status: "saved" });
    expect(mocks.rpc).toHaveBeenCalledWith("create_invite", {
      p_label: "Telegram",
      p_max_uses: 25,
      p_expires_at: "2026-10-20T12:00:00.000Z",
    });
  });

  it("creates a link that never expires, and explains when it isn't the admin", async () => {
    await run(createInvite(idle, form({ label: "", maxUses: "", expiresIn: "never" })));
    expect(mocks.rpc).toHaveBeenCalledWith("create_invite", { p_label: "", p_max_uses: null, p_expires_at: null });
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "42501" } });
    expect((await run(createInvite(idle, form({ label: "", maxUses: "", expiresIn: "never" })))).state).toEqual({
      status: "error",
      message: "Only the admin can manage invite links.",
    });
  });

  it("switches a link off", async () => {
    expect((await run(revokeInvite(idle, form({ id: APPLICATION_ID })))).state).toEqual({ status: "saved", message: "Link switched off." });
    expect(mocks.rpc).toHaveBeenCalledWith("revoke_invite", { p_invite: APPLICATION_ID });
    expect(mocks.refresh).toHaveBeenCalled();
  });
});

describe("updateProfile", () => {
  const profile = {
    displayName: "Amara",
    tiktok: "tiktok.com/@amara",
    youtube: "",
    instagram: "",
    linkedin: "",
    niches: ["ai"],
    followers: "12k",
    avgViews: "3000",
    country: "gb",
    bio: "Builder.",
    ratePerPost: "150",
    rateCurrency: "USDC",
  };

  it("updates only the caller's own row, with the fields creators may change", async () => {
    const { state } = await run(updateProfile(idle, form(profile)));
    expect(state).toEqual({ status: "saved", message: "Profile saved." });
    expect(mocks.update).toHaveBeenCalledWith({
      display_name: "Amara",
      tiktok_url: "https://tiktok.com/@amara",
      youtube_url: null,
      instagram_url: null,
      linkedin_url: null,
      niches: ["ai"],
      followers: 12000,
      avg_views: 3000,
      country: "GB",
      bio: "Builder.",
      rate_per_post: "150",
      rate_currency: "USDC",
    });
    expect(mocks.eq).toHaveBeenCalledWith("id", "8a7d5c1e-0000-4000-8000-000000000001");
  });

  it("asks them to sign in again when the session has gone", async () => {
    mocks.claims = null;
    expect((await run(updateProfile(idle, form(profile)))).state).toMatchObject({ status: "error", message: expect.stringContaining("Sign in again") });
    expect(mocks.update).not.toHaveBeenCalled();
  });
});

describe("saveAvatar", () => {
  const me = "8a7d5c1e-0000-4000-8000-000000000001";
  const photo = `https://project.supabase.co/storage/v1/object/public/avatars/${me}/avatar.webp?v=1760540000000`;

  it("saves the caller's own uploaded photo", async () => {
    expect(await saveAvatar(photo)).toEqual({ status: "saved", message: "Photo saved." });
    expect(mocks.update).toHaveBeenCalledWith({ avatar_url: photo });
    expect(mocks.eq).toHaveBeenCalledWith("id", me);
    expect(mocks.remove).not.toHaveBeenCalled();
    expect(mocks.refresh).toHaveBeenCalled();
  });

  it("refuses any other address: another person's folder, another project, or a lookalike", async () => {
    for (const url of [
      photo.replace(me, "8a7d5c1e-0000-4000-8000-000000000002"),
      photo.replace("project.supabase.co", "evil.supabase.co"),
      `${photo}&x=1`,
      "https://tracker.example/pixel.gif",
      `https://project.supabase.co/storage/v1/object/public/avatars/${me}/avatar.webp.evil`,
    ]) {
      expect(await saveAvatar(url), url).toEqual({ status: "error", message: "That photo didn't upload. Try again." });
    }
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("clears the photo and removes the file", async () => {
    expect(await saveAvatar(null)).toEqual({ status: "saved", message: "Photo removed." });
    expect(mocks.update).toHaveBeenCalledWith({ avatar_url: null });
    expect(mocks.remove).toHaveBeenCalledWith([`${me}/avatar.webp`]);
  });

  it("asks them to sign in again when the session has gone", async () => {
    mocks.claims = null;
    expect(await saveAvatar(photo)).toEqual({ status: "error", message: "Your sign-in has expired. Sign in again." });
  });
});

describe("savePayoutDetails", () => {
  it("sends only the chosen method's fields, and emails the confirmation after the response", async () => {
    mocks.rpc.mockResolvedValue({ data: OUTBOX_ID, error: null });
    const { state } = await run(
      savePayoutDetails(idle, form({ method: "crypto", asset: "USDC", network: "base", wallet: EVM, bankName: "Ignored" })),
    );
    expect(state).toEqual({ status: "saved", message: "Saved. We've emailed you to confirm the change." });
    expect(mocks.rpc).toHaveBeenCalledWith("set_payout_details", {
      p_method: "crypto",
      p_crypto_asset: "USDC",
      p_crypto_network: "base",
      p_wallet_address: EVM,
      p_bank_country: null,
      p_bank_name: null,
      p_account_name: null,
      p_account_number: null,
      p_bank_code: null,
      p_other_details: null,
    });
    expect(mocks.after).toHaveBeenCalledTimes(1);
  });

  it("checks the wallet against its network before anything is saved", async () => {
    const { state } = await run(savePayoutDetails(idle, form({ method: "crypto", asset: "USDC", network: "solana", wallet: EVM })));
    expect(state).toMatchObject({ status: "error", fieldErrors: { wallet: expect.stringContaining("doesn't look like an address") } });
    expect(mocks.rpc).not.toHaveBeenCalled();
  });

  it("explains when the account isn't a creator", async () => {
    mocks.rpc.mockResolvedValue({ data: null, error: { code: "42501" } });
    expect((await run(savePayoutDetails(idle, form({ method: "other", otherDetails: "Wise" })))).state).toEqual({
      status: "error",
      message: "Only approved creators can change this.",
    });
  });
});

describe("inviteStateFromError", () => {
  it("reads redeem_invite's refusals, and ignores other errors", () => {
    expect(inviteStateFromError({ code: "P0410", message: "invite_expired" })).toBe("expired");
    expect(inviteStateFromError({ code: "P0410", message: "something odd" })).toBe("unknown");
    expect(inviteStateFromError({ code: "42501", message: "invite_expired" })).toBeNull();
    expect(inviteStateFromError(null)).toBeNull();
  });
});
