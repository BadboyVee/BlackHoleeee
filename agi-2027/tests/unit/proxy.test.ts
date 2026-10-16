import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

type CookieToSet = { name: string; value: string; options: Record<string, unknown> };
type CookieMethods = {
  getAll: () => { name: string; value: string }[];
  setAll: (cookies: CookieToSet[], headers: Record<string, string>) => void;
};

const mocks = vi.hoisted(() => ({
  claims: null as Record<string, unknown> | null,
  /** The profile row the database returns, or an error. */
  profile: null as { role: string; status: string } | null,
  profileError: null as { code: string } | null,
  /** Cookies the session refresh writes while getClaims runs. */
  refresh: null as CookieToSet[] | null,
  profileReads: 0,
  cookieMethods: null as CookieMethods | null,
}));

vi.mock("@supabase/ssr", () => ({
  createServerClient: (_url: string, _key: string, options: { cookies: CookieMethods }) => {
    mocks.cookieMethods = options.cookies;
    return {
      auth: {
        getClaims: async () => {
          if (mocks.refresh) {
            options.cookies.setAll(mocks.refresh, {
              "Cache-Control": "private, no-cache, no-store, must-revalidate, max-age=0",
              Expires: "0",
              Pragma: "no-cache",
            });
          }
          return { data: mocks.claims ? { claims: mocks.claims } : null, error: null };
        },
      },
      from: (table: string) => {
        expect(table).toBe("profiles");
        const query = {
          select: () => query,
          eq: () => query,
          maybeSingle: async () => {
            mocks.profileReads += 1;
            return { data: mocks.profileError ? null : mocks.profile, error: mocks.profileError };
          },
        };
        return query;
      },
    };
  },
}));

const { config, proxy } = await import("@/proxy");

const USER = "8a7d5c1e-0000-4000-8000-000000000001";

function request(path: string) {
  return new NextRequest(new URL(path, "https://agi2027.example"));
}

function signIn(role?: string) {
  mocks.claims = { sub: USER, ...(role ? { user_role: role } : {}) };
}

function location(response: Response) {
  return response.headers.get("location");
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.supabase.co");
  vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x");
  mocks.claims = null;
  mocks.profile = null;
  mocks.profileError = null;
  mocks.refresh = null;
  mocks.profileReads = 0;
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe("config", () => {
  it("runs on the private areas and the sign-in pages, nothing public", () => {
    expect(config.matcher).toEqual([
      "/admin/:path*",
      "/dashboard/:path*",
      "/application/:path*",
      "/styleguide/:path*",
      "/login",
      "/signup",
      "/reset-password",
      "/invite/:path*",
    ]);
  });
});

describe("without Supabase settings", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
  });

  it("keeps the demo apps open on preview links and laptops", async () => {
    for (const stage of ["preview", "development", ""]) {
      vi.stubEnv("AGI_DEPLOY_STAGE", stage);
      for (const path of ["/admin", "/dashboard", "/application", "/styleguide", "/login"]) {
        const response = await proxy(request(path));
        expect(location(response), `${stage} ${path}`).toBeNull();
        expect(response.headers.get("x-middleware-next")).toBe("1");
      }
    }
  });

  it("sends live-site visitors home from the private areas, but shows the sign-in pages", async () => {
    vi.stubEnv("AGI_DEPLOY_STAGE", "production");
    for (const path of ["/admin/campaigns?status=live", "/dashboard", "/application", "/styleguide"]) {
      const response = await proxy(request(path));
      expect(response.status, path).toBe(307);
      expect(location(response), path).toBe("https://agi2027.example/");
    }
    expect(location(await proxy(request("/login")))).toBeNull();
  });
});

describe("signed-out visitors", () => {
  it("go to sign in from a private page, which remembers the page and its query", async () => {
    expect(location(await proxy(request("/admin")))).toBe("https://agi2027.example/login?next=%2Fadmin");
    expect(location(await proxy(request("/dashboard/campaigns/x?tab=brief")))).toBe(
      "https://agi2027.example/login?next=%2Fdashboard%2Fcampaigns%2Fx%3Ftab%3Dbrief",
    );
  });

  it("go back to ask for a new link from the reset page", async () => {
    expect(location(await proxy(request("/reset-password")))).toBe("https://agi2027.example/forgot-password?status=expired");
  });

  it("can open sign in and sign up", async () => {
    for (const path of ["/login?next=%2Fadmin", "/signup"]) {
      const response = await proxy(request(path));
      expect(location(response), path).toBeNull();
    }
    expect(mocks.profileReads).toBe(0);
  });
});

describe("signed-in people", () => {
  it("open their own area straight from the token's role, with no database read", async () => {
    signIn("admin");
    expect(location(await proxy(request("/admin/payouts")))).toBeNull();
    signIn("creator");
    expect(location(await proxy(request("/dashboard/earnings")))).toBeNull();
    expect(mocks.profileReads).toBe(0);
  });

  it("go to their own home when they open someone else's area", async () => {
    signIn("creator");
    mocks.profile = { role: "creator", status: "active" };
    expect(location(await proxy(request("/admin")))).toBe("https://agi2027.example/dashboard");
    signIn("team");
    mocks.profile = { role: "team", status: "active" };
    expect(location(await proxy(request("/admin/settings")))).toBe("https://agi2027.example/admin");
  });

  it("get in when the database says they were just promoted, though the token is older", async () => {
    signIn("applicant");
    mocks.profile = { role: "admin", status: "active" };
    expect(location(await proxy(request("/admin")))).toBeNull();
    expect(mocks.profileReads).toBe(1);
  });

  it("are routed by the database when the hook isn't on yet", async () => {
    signIn();
    mocks.profile = { role: "creator", status: "active" };
    expect(location(await proxy(request("/dashboard")))).toBeNull();
    expect(location(await proxy(request("/admin")))).toBe("https://agi2027.example/dashboard");
  });

  it("leave the application page once the database says they're approved", async () => {
    signIn("applicant");
    mocks.profile = { role: "creator", status: "active" };
    expect(location(await proxy(request("/application")))).toBe("https://agi2027.example/dashboard");
    mocks.profile = { role: "applicant", status: "active" };
    expect(location(await proxy(request("/application")))).toBeNull();
  });

  it("skip sign in, going where they were headed when they may", async () => {
    signIn("admin");
    mocks.profile = { role: "admin", status: "active" };
    expect(location(await proxy(request("/login")))).toBe("https://agi2027.example/admin");
    expect(location(await proxy(request("/login?next=%2Fadmin%2Freview")))).toBe("https://agi2027.example/admin/review");
    expect(location(await proxy(request("/signup?next=https%3A%2F%2Fevil.example")))).toBe("https://agi2027.example/admin");
  });

  it("with an account that isn't active, see the sign-in page's explanation instead of the apps", async () => {
    signIn("none");
    mocks.profile = { role: "creator", status: "suspended" };
    expect(location(await proxy(request("/dashboard")))).toBe("https://agi2027.example/login?status=unavailable");
    expect(location(await proxy(request("/login?status=unavailable")))).toBeNull();
  });

  it("can set a new password whatever their role", async () => {
    signIn("creator");
    expect(location(await proxy(request("/reset-password")))).toBeNull();
  });
});

describe("when the database doesn't answer", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    mocks.profileError = { code: "PGRST000" };
  });

  it("keeps the token's answer", async () => {
    signIn("creator");
    expect(location(await proxy(request("/admin")))).toBe("https://agi2027.example/dashboard");
  });

  it("sends people without a role claim to sign in again, rather than guess", async () => {
    signIn();
    expect(location(await proxy(request("/admin")))).toBe("https://agi2027.example/login?error=auth");
    expect(location(await proxy(request("/login?error=auth")))).toBeNull();
  });
});

describe("session refresh", () => {
  const refreshed: CookieToSet[] = [
    { name: "sb-project-auth-token", value: "new-token", options: { path: "/", sameSite: "lax", httpOnly: false } },
  ];

  it("passes refreshed cookies to the page and the browser, with no-cache headers", async () => {
    signIn("creator");
    mocks.refresh = refreshed;
    const response = await proxy(request("/dashboard"));
    expect(location(response)).toBeNull();
    expect(response.cookies.get("sb-project-auth-token")?.value).toBe("new-token");
    expect(response.headers.get("cache-control")).toContain("no-store");
    // The page rendering after the proxy reads the fresh cookie too.
    expect(response.headers.get("x-middleware-request-cookie") ?? response.headers.get("x-middleware-override-headers")).toBeTruthy();
  });

  it("keeps refreshed cookies on a redirect too", async () => {
    signIn("creator");
    mocks.profile = { role: "creator", status: "active" };
    mocks.refresh = refreshed;
    const response = await proxy(request("/admin"));
    expect(location(response)).toBe("https://agi2027.example/dashboard");
    expect(response.cookies.get("sb-project-auth-token")?.value).toBe("new-token");
    expect(response.headers.get("cache-control")).toContain("no-store");
  });

  it("refreshes the session on invite links, and never sends anyone away from them", async () => {
    mocks.refresh = refreshed;
    for (const role of [undefined, "creator", "applicant"]) {
      if (role) signIn(role);
      else mocks.claims = null;
      const response = await proxy(request("/invite/7c2e9a41d03f5b86"));
      expect(location(response), String(role)).toBeNull();
      expect(response.cookies.get("sb-project-auth-token")?.value).toBe("new-token");
    }
    // Nothing to decide there, so no role lookup either.
    expect(mocks.profileReads).toBe(0);
  });

  it("reads the request's own cookies", async () => {
    const withCookie = new NextRequest(new URL("/dashboard", "https://agi2027.example"), {
      headers: { cookie: "sb-project-auth-token=old-token" },
    });
    await proxy(withCookie);
    expect(mocks.cookieMethods?.getAll()).toEqual([{ name: "sb-project-auth-token", value: "old-token" }]);
  });
});
