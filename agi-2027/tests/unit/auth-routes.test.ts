import { describe, expect, it } from "vitest";

import { adminNavGroups } from "@/components/admin/admin-nav";
import {
  accessFor,
  ACCOUNT_UNAVAILABLE_PATH,
  ADMIN_ONLY_PATHS,
  areaFor,
  destinationFor,
  loginHref,
  nextFromUrlOrPath,
  parseRoleClaim,
  roleHome,
  safeNextPath,
  signedOutRedirect,
  type RoleClaim,
} from "@/lib/auth/routes";

const ROLE_CLAIMS: RoleClaim[] = ["admin", "team", "creator", "applicant", "none"];

describe("parseRoleClaim", () => {
  it("reads the roles the access token hook writes", () => {
    for (const role of ROLE_CLAIMS) expect(parseRoleClaim(role)).toBe(role);
  });

  it("ignores anything else, such as a token from before the hook was on", () => {
    for (const value of [undefined, null, "", "owner", "Admin", 1, { role: "admin" }]) {
      expect(parseRoleClaim(value), String(value)).toBeUndefined();
    }
  });
});

describe("roleHome", () => {
  it("sends each role to its own app", () => {
    expect(roleHome("admin")).toBe("/admin");
    expect(roleHome("team")).toBe("/admin");
    expect(roleHome("creator")).toBe("/dashboard");
    expect(roleHome("applicant")).toBe("/application");
    expect(roleHome("none")).toBe(ACCOUNT_UNAVAILABLE_PATH);
  });
});

describe("areaFor", () => {
  it("knows every guarded part of the site", () => {
    const cases: Record<string, ReturnType<typeof areaFor>> = {
      "/admin": "admin",
      "/admin/campaigns/new": "admin",
      "/dashboard": "creator",
      "/dashboard/campaigns/abc": "creator",
      "/application": "applicant",
      "/styleguide": "staff",
      "/login": "guest",
      "/signup": "guest",
      "/reset-password": "session",
      "/invite/7c2e9a41d03f5b86": "open",
    };
    for (const [path, area] of Object.entries(cases)) expect(areaFor(path), path).toBe(area);
  });

  it("leaves public pages, and look-alike paths, alone", () => {
    for (const path of ["/", "/book", "/campaigns", "/apply", "/forgot-password", "/administrator", "/dashboards", "/login/x", "/auth/callback", "/invite", "/invites"]) {
      expect(areaFor(path), path).toBeNull();
    }
  });
});

describe("ADMIN_ONLY_PATHS", () => {
  it("matches the admin-only items in the admin's navigation", () => {
    const adminOnly = adminNavGroups.flatMap((group) => group.items).filter((item) => item.adminOnly);
    expect([...ADMIN_ONLY_PATHS].sort()).toEqual(adminOnly.map((item) => item.href).sort());
  });
});

describe("accessFor", () => {
  const allowed = { kind: "allow" };
  const goTo = (to: string) => ({ kind: "redirect", to });

  it("lets everyone open an invite link, whatever their role", () => {
    for (const role of ["admin", "team", "creator", "applicant", "none"] as const) {
      expect(accessFor("/invite/7c2e9a41d03f5b86", role), role).toEqual(allowed);
    }
  });

  it("lets admin open every admin page, team all but the admin-only ones", () => {
    expect(accessFor("/admin/payouts", "admin")).toEqual(allowed);
    expect(accessFor("/admin/campaigns", "team")).toEqual(allowed);
    for (const path of ADMIN_ONLY_PATHS) {
      expect(accessFor(path, "admin"), path).toEqual(allowed);
      expect(accessFor(path, "team"), path).toEqual(goTo("/admin"));
      expect(accessFor(`${path}/x`, "team"), path).toEqual(goTo("/admin"));
    }
  });

  it("keeps creators and applicants out of the admin, sending them to their own home", () => {
    expect(accessFor("/admin", "creator")).toEqual(goTo("/dashboard"));
    expect(accessFor("/admin/campaigns", "applicant")).toEqual(goTo("/application"));
  });

  it("opens the creator portal to creators, and to staff to see what creators see", () => {
    for (const role of ["creator", "admin", "team"] as const) expect(accessFor("/dashboard", role), role).toEqual(allowed);
    expect(accessFor("/dashboard/earnings", "applicant")).toEqual(goTo("/application"));
  });

  it("shows the application page only to applicants", () => {
    expect(accessFor("/application", "applicant")).toEqual(allowed);
    expect(accessFor("/application", "creator")).toEqual(goTo("/dashboard"));
    expect(accessFor("/application", "team")).toEqual(goTo("/admin"));
  });

  it("shows the design system to staff only", () => {
    expect(accessFor("/styleguide", "team")).toEqual(allowed);
    expect(accessFor("/styleguide", "creator")).toEqual(goTo("/dashboard"));
  });

  it("sends an account that isn't active to the sign-in page, which explains, from everywhere private", () => {
    for (const path of ["/admin", "/dashboard", "/application", "/styleguide"]) {
      expect(accessFor(path, "none"), path).toEqual(goTo(ACCOUNT_UNAVAILABLE_PATH));
    }
    expect(accessFor("/login", "none")).toEqual(allowed);
  });

  it("moves signed-in people past sign in and sign up, to where they were going if they may", () => {
    expect(accessFor("/login", "creator")).toEqual(goTo("/dashboard"));
    expect(accessFor("/signup", "admin")).toEqual(goTo("/admin"));
    expect(accessFor("/login", "admin", "/admin/campaigns?status=live")).toEqual(goTo("/admin/campaigns?status=live"));
    expect(accessFor("/login", "applicant", "/dashboard/campaigns/x")).toEqual(goTo("/application"));
  });

  it("lets anyone signed in set a new password, and leaves public pages alone", () => {
    for (const role of ROLE_CLAIMS) {
      expect(accessFor("/reset-password", role), role).toEqual(allowed);
      expect(accessFor("/book", role), role).toEqual(allowed);
    }
  });
});

describe("signedOutRedirect", () => {
  it("sends signed-out visitors to sign in, remembering the page and its query", () => {
    expect(signedOutRedirect("/admin")).toBe("/login?next=%2Fadmin");
    expect(signedOutRedirect("/dashboard/campaigns/x", "?tab=brief")).toBe(
      "/login?next=%2Fdashboard%2Fcampaigns%2Fx%3Ftab%3Dbrief",
    );
    expect(signedOutRedirect("/application")).toBe("/login?next=%2Fapplication");
    expect(signedOutRedirect("/styleguide")).toBe("/login?next=%2Fstyleguide");
  });

  it("sends a reset page without its sign-in back to ask for a new link", () => {
    expect(signedOutRedirect("/reset-password")).toBe("/forgot-password?status=expired");
  });

  it("lets signed-out visitors open public pages and the sign-in pages", () => {
    for (const path of ["/", "/book", "/login", "/signup", "/forgot-password"]) expect(signedOutRedirect(path), path).toBeNull();
  });
});

describe("destinationFor", () => {
  it("goes where they were heading when their role may open it", () => {
    expect(destinationFor("admin", "/admin/review")).toBe("/admin/review");
    expect(destinationFor("creator", "/dashboard/campaigns/abc?tab=brief")).toBe("/dashboard/campaigns/abc?tab=brief");
    expect(destinationFor("creator", "/campaigns")).toBe("/campaigns");
  });

  it("goes to the role's home otherwise", () => {
    expect(destinationFor("applicant", "/dashboard/campaigns/abc")).toBe("/application");
    expect(destinationFor("team", "/admin/payouts")).toBe("/admin");
    expect(destinationFor("creator", null)).toBe("/dashboard");
    expect(destinationFor("creator", "/login")).toBe("/dashboard");
    expect(destinationFor("creator", "/reset-password")).toBe("/dashboard");
    expect(destinationFor("admin", "https://evil.example/admin")).toBe("/admin");
    expect(destinationFor("none", "/dashboard")).toBe(ACCOUNT_UNAVAILABLE_PATH);
  });
});

describe("safeNextPath", () => {
  it("keeps same-site paths with their query", () => {
    expect(safeNextPath("/dashboard")).toBe("/dashboard");
    expect(safeNextPath(" /admin/campaigns?status=live ")).toBe("/admin/campaigns?status=live");
    expect(safeNextPath("/dashboard/campaigns/a%20b")).toBe("/dashboard/campaigns/a%20b");
  });

  it("refuses anything that could leave the site or loop through the auth routes", () => {
    for (const value of [
      null,
      undefined,
      "",
      "dashboard",
      "https://evil.example",
      "//evil.example",
      "///evil.example",
      "/\\evil.example",
      "\\/evil.example",
      "/\tevil",
      "/%0d%0aSet-Cookie:x",
      "javascript:alert(1)",
      "/auth/callback?code=x",
      "/auth",
    ]) {
      const result = safeNextPath(value);
      // Encoded line breaks stay encoded, so they're harmless path text; everything else is refused.
      if (value === "/%0d%0aSet-Cookie:x") expect(result).toBe("/%0d%0aSet-Cookie:x");
      else expect(result, String(value)).toBeNull();
    }
  });
});

describe("loginHref", () => {
  it("adds next only for a real destination", () => {
    expect(loginHref("/dashboard/earnings")).toBe("/login?next=%2Fdashboard%2Fearnings");
    expect(loginHref("/")).toBe("/login");
    expect(loginHref("https://evil.example")).toBe("/login");
    expect(loginHref(undefined)).toBe("/login");
  });
});

describe("nextFromUrlOrPath", () => {
  const origin = "https://agi2027.netlify.app";

  it("accepts a path, or a full URL on this site reduced to its path", () => {
    expect(nextFromUrlOrPath("/dashboard", origin)).toBe("/dashboard");
    expect(nextFromUrlOrPath(`${origin}/dashboard/campaigns/x?tab=brief`, origin)).toBe("/dashboard/campaigns/x?tab=brief");
  });

  it("refuses full URLs on other sites", () => {
    expect(nextFromUrlOrPath("https://evil.example/dashboard", origin)).toBeNull();
    expect(nextFromUrlOrPath("http://agi2027.netlify.app/dashboard", origin)).toBeNull();
    expect(nextFromUrlOrPath("not a url", origin)).toBeNull();
  });
});
