import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { siteConfig } from "@/lib/site";

const PUBLIC_PATHS = ["/", "/campaigns", "/book", "/apply", "/terms", "/privacy"];
const PRIVATE_PATHS = ["/admin", "/dashboard", "/styleguide", "/api"];

describe("sitemap", () => {
  const entries = sitemap();

  it("lists exactly the public pages", () => {
    expect(entries.map((entry) => new URL(entry.url).pathname)).toEqual(PUBLIC_PATHS);
  });

  it("uses absolute URLs on the site's own origin", () => {
    const origin = new URL(siteConfig.url).origin;
    for (const entry of entries) {
      const url = new URL(entry.url);
      expect(["http:", "https:"]).toContain(url.protocol);
      expect(url.origin).toBe(origin);
      expect(entry.url.startsWith(origin)).toBe(true);
    }
  });

  it("leaves out sign in, the portal, the admin and the styleguide", () => {
    for (const entry of entries) {
      const { pathname } = new URL(entry.url);
      for (const path of [...PRIVATE_PATHS, "/login", "/signup"]) {
        expect(pathname === path || pathname.startsWith(`${path}/`)).toBe(false);
      }
    }
  });
});

describe("robots", () => {
  const result = robots();
  const rules = Array.isArray(result.rules) ? result.rules : [result.rules];
  const everyone = rules.find((rule) => rule.userAgent === "*");

  it("lets every crawler read the public site", () => {
    expect(everyone?.allow).toBe("/");
  });

  it("keeps crawlers out of the private areas", () => {
    expect(everyone?.disallow).toEqual(expect.arrayContaining(PRIVATE_PATHS));
  });

  it("never blocks a page the sitemap lists", () => {
    const disallow = ([] as string[]).concat(everyone?.disallow ?? []);
    for (const path of PUBLIC_PATHS) {
      expect(disallow.some((rule) => rule !== "/" && path.startsWith(rule))).toBe(false);
    }
  });

  it("links the sitemap with an absolute URL", () => {
    expect(result.sitemap).toBe(new URL("/sitemap.xml", siteConfig.url).toString());
    expect(String(result.sitemap)).toMatch(/^https?:\/\/.+\/sitemap\.xml$/);
  });
});

describe("canonical URLs", () => {
  // Read as text: importing the pages would pull in the whole home page, 3D scenes included.
  const source = (page: string) =>
    readFileSync(path.resolve(import.meta.dirname, "../../src/app/(marketing)", page.slice(1), "page.tsx"), "utf8");

  it("gives every page in the sitemap a canonical URL of its own path", () => {
    for (const page of PUBLIC_PATHS) {
      expect(source(page), page).toContain(`canonical: "${page}"`);
    }
  });
});
