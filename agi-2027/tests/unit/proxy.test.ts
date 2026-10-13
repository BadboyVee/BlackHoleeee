import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { config, isPreviewOnlyPath, proxy } from "@/proxy";

afterEach(() => {
  vi.unstubAllEnvs();
});

function request(path: string) {
  return new NextRequest(new URL(path, "https://agi2027.example"));
}

describe("isPreviewOnlyPath", () => {
  it("covers the demo apps and the styleguide, nothing public", () => {
    for (const path of ["/admin", "/admin/campaigns/new", "/dashboard", "/dashboard/campaigns/x", "/styleguide"]) {
      expect(isPreviewOnlyPath(path), path).toBe(true);
    }
    for (const path of ["/", "/campaigns", "/book", "/apply", "/login", "/administrator", "/dashboards"]) {
      expect(isPreviewOnlyPath(path), path).toBe(false);
    }
  });

  it("matches what the proxy config runs on", () => {
    expect(config.matcher).toEqual(["/admin/:path*", "/dashboard/:path*", "/styleguide/:path*"]);
  });
});

describe("proxy", () => {
  it("sends live-site visitors home from the demo apps", () => {
    vi.stubEnv("AGI_DEPLOY_STAGE", "production");
    const response = proxy(request("/admin/campaigns?status=live"));
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://agi2027.example/");
  });

  it("lets preview links and local development through", () => {
    for (const stage of ["preview", "development", ""]) {
      vi.stubEnv("AGI_DEPLOY_STAGE", stage);
      const response = proxy(request("/dashboard"));
      expect(response.headers.get("location"), stage).toBeNull();
      expect(response.headers.get("x-middleware-next"), stage).toBe("1");
    }
  });

  it("never touches public pages, even on the live site", () => {
    vi.stubEnv("AGI_DEPLOY_STAGE", "production");
    const response = proxy(request("/campaigns"));
    expect(response.headers.get("location")).toBeNull();
  });
});
