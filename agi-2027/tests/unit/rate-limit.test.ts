import { createHash } from "node:crypto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ rpc: vi.fn() }));

vi.mock("server-only", () => ({}));
vi.mock("@/lib/supabase/admin", () => ({ createAdminClient: () => ({ rpc: mocks.rpc }) }));

const { hitRateLimit, rateKey } = await import("@/lib/rate-limit");

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.co");
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x");
  vi.stubEnv("SUPABASE_SECRET_KEY", "sb_secret_x");
  vi.stubEnv("RATE_LIMIT_SALT", "pepper");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  mocks.rpc.mockReset();
});

describe("rateKey", () => {
  it("is a salted SHA-256, never the value itself", () => {
    expect(rateKey("ada@kled.ai")).toBe(createHash("sha256").update("pepperada@kled.ai").digest("hex"));
    expect(rateKey("ada@kled.ai")).not.toContain("ada");
  });
});

describe("hitRateLimit", () => {
  it("sends the kind and the hashed value, and passes on the answer", async () => {
    mocks.rpc.mockResolvedValueOnce({ data: true, error: null }).mockResolvedValueOnce({ data: false, error: null });
    expect(await hitRateLimit("sign_in_email", "ada@kled.ai")).toBe(true);
    expect(await hitRateLimit("sign_in_email", "ada@kled.ai")).toBe(false);
    expect(mocks.rpc).toHaveBeenCalledWith("hit_rate_limit", { p_kind: "sign_in_email", p_key: rateKey("ada@kled.ai") });
  });

  it("lets the try through when the database can't answer, so an outage locks nobody out", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    mocks.rpc.mockResolvedValueOnce({ data: null, error: { code: "PGRST000", message: "down" } });
    expect(await hitRateLimit("sign_in_ip", "203.0.113.7")).toBe(true);
    mocks.rpc.mockRejectedValueOnce(new TypeError("fetch failed"));
    expect(await hitRateLimit("sign_in_ip", "203.0.113.7")).toBe(true);
  });

  it("does nothing when the database isn't configured", async () => {
    vi.stubEnv("SUPABASE_SECRET_KEY", "");
    expect(await hitRateLimit("sign_up_ip", "203.0.113.7")).toBe(true);
    expect(mocks.rpc).not.toHaveBeenCalled();
  });
});
