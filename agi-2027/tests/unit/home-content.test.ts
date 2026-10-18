import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { HomeHero } from "@/components/marketing/home-hero";
import { BrandsMarquee } from "@/components/marketing/sections/brands";
import { ProofSection } from "@/components/marketing/sections/proof";
import { StatsSection } from "@/components/marketing/sections/stats";
import { countText } from "@/components/ui/count-up";
import { combinedFollowers, compactFollowers, creatorRoster } from "@/lib/creator-roster";
import { brands, stats } from "@/lib/marketing-content";
import {
  parseXCount,
  showcaseBrands,
  showcasePosts,
  STATS_AS_OF,
  totalViews,
  type ShowcasePost,
} from "@/lib/showcase-posts";

/** The page's text without tags, entities decoded, on one line. */
function textOf(html: string) {
  return html
    .replace(/<[^>]+>/g, " ")
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

// The eight brand names that were made up before the owner sent real clients.
const INVENTED_BRANDS = ["Nebula", "Vectorline", "Orbitar", "Lumen Labs", "Parallax", "Quanta", "Helix", "Northwind"];

describe("parseXCount", () => {
  it("reads counts the way X writes them, exactly", () => {
    expect(parseXCount("3.7M")).toBe(3_700_000);
    expect(parseXCount("1.8M")).toBe(1_800_000);
    expect(parseXCount("171K")).toBe(171_000);
    expect(parseXCount("2.7K")).toBe(2_700);
    expect(parseXCount("456K")).toBe(456_000);
    expect(parseXCount("769")).toBe(769);
    expect(parseXCount("6,237")).toBe(6_237);
    expect(parseXCount("1.2B")).toBe(1_200_000_000);
    expect(parseXCount(" 3K ")).toBe(3_000);
  });

  it("refuses anything that isn't a count", () => {
    for (const value of [undefined, "", "K", "3.7", "1,23", "3.7MM", "-5", "about 3K", "3.7 M"]) {
      expect(parseXCount(value), String(value)).toBeNull();
    }
  });
});

describe("totalViews and showcaseBrands", () => {
  const post = (brand: string, views?: string) => ({ brand, stats: views ? { views } : {} }) as ShowcasePost;

  it("adds up the views and says when one is missing", () => {
    expect(totalViews([post("A", "3.7M"), post("B", "171K")])).toEqual({ views: 3_871_000, partial: false });
    expect(totalViews([post("A", "3.7M"), post("B")])).toEqual({ views: 3_700_000, partial: true });
    expect(totalViews([])).toEqual({ views: 0, partial: false });
  });

  it("counts each brand once, even with two posts for it", () => {
    expect(showcaseBrands([post("micro1"), post("Kled AI"), post("micro1")])).toEqual(["micro1", "Kled AI"]);
  });

  it("names the brand on every real post: Ali Ansari posts for micro1", () => {
    expect(showcasePosts.map((item) => [item.author.handle, item.brand])).toEqual([
      ["useKled", "Kled AI"],
      ["aliansarinik", "micro1"],
      ["MaincodeAU", "Maincode"],
      ["aliansarinik", "micro1"],
      ["hedwigdotco", "Hedwig"],
    ]);
    expect(showcaseBrands(showcasePosts)).toEqual(["Kled AI", "micro1", "Maincode", "Hedwig"]);
  });

  it("adds up the real posts' views: 3.7M, 171K, 1.8M and 456K, one post unknown", () => {
    expect(totalViews(showcasePosts)).toEqual({ views: 6_127_000, partial: true });
  });
});

describe("countText", () => {
  it("writes numbers without Intl, rounding compact ones down", () => {
    expect(countText(128_660, "compact")).toBe("128.6K");
    expect(countText(6_127_000, "compact")).toBe("6.1M");
    expect(countText(980, "compact")).toBe("980");
    expect(countText(0, "compact")).toBe("0");
    expect(countText(14, "plain")).toBe("14");
    expect(countText(12_400_000, "plain")).toBe("12,400,000");
    expect(countText(13.9, "plain")).toBe("13");
  });

  it("matches the roster's own follower format", () => {
    for (const value of [9_560, 26_300, 128_660, 1_250_000]) {
      expect(countText(value, "compact")).toBe(compactFollowers(value));
    }
  });
});

describe("stats", () => {
  it("come from the data, not typed in", () => {
    expect(stats.map(({ label, value, format, suffix }) => ({ label, value, format, suffix }))).toEqual([
      { label: "Combined followers on X", value: combinedFollowers(creatorRoster), format: "compact", suffix: undefined },
      { label: "Views on our clients' launch posts", value: 6_127_000, format: "compact", suffix: "+" },
      { label: "Brands launched", value: 4, format: "plain", suffix: undefined },
      { label: "Creators in the network", value: creatorRoster.length, format: "plain", suffix: undefined },
    ]);
    expect(stats[0].value).toBe(128_660);
    expect(stats[3].value).toBe(14);
  });

  it("say which day the numbers from X are from", () => {
    expect(stats[0].asOf).toBe("2026-10-17");
    expect(stats[1].asOf).toBe(STATS_AS_OF);
  });

  it("never claim a monthly rate or views on the creators' own posts", () => {
    for (const stat of stats) expect(stat.label).not.toMatch(/month|creators' posts/i);
  });

  it("render the real numbers, rounded down, with the dates", () => {
    const text = textOf(renderToStaticMarkup(createElement(StatsSection)));
    expect(text).toContain("128.6K Combined followers on X From X, 17 Oct 2026");
    expect(text).toContain("6.1M+ Views on our clients' launch posts From X, 12 Oct 2026");
    expect(text).toContain("4 Brands launched");
    expect(text).toContain("14 Creators in the network");
    for (const made_up of ["12.4M", "85M", "140", "15 Creators", "every month"]) expect(text).not.toContain(made_up);
  });
});

describe("brand strip", () => {
  it("lists exactly the owner's four real clients", () => {
    expect(brands.map((brand) => brand.name)).toEqual(["Kled AI", "micro1", "Maincode", "Hedwig"]);
  });

  it("includes every brand we show a launch post for", () => {
    const names = brands.map((brand) => brand.name);
    for (const brand of showcaseBrands(showcasePosts)) expect(names).toContain(brand);
  });

  it("uses only logos the brands really use, from their own X accounts, and no logo for micro1", () => {
    for (const brand of brands) {
      if (!brand.logo) continue;
      expect(existsSync(join(process.cwd(), "public", brand.logo.src)), brand.logo.src).toBe(true);
      const own = showcasePosts.find((post) => post.brand === brand.name && post.author.avatar === brand.logo?.src);
      expect(own, `${brand.name}'s logo is its own account's picture`).toBeDefined();
      expect(own?.author.name).toBe(brand.name);
      expect(brand.logo.shape).toBe(own?.author.avatarShape);
    }
    expect(brands.find((brand) => brand.name === "micro1")?.logo).toBeNull();
  });

  it("renders the four names for screen readers once, and none of the old ones", () => {
    const html = renderToStaticMarkup(createElement(BrandsMarquee));
    const readable = [...html.matchAll(/<li>([^<]*)<\/li>/g)].map((match) => match[1]);
    expect(readable).toEqual(["Kled AI", "micro1", "Maincode", "Hedwig"]);
    for (const name of INVENTED_BRANDS) expect(html).not.toContain(name);
  });

  it("loops two identical halves, each repeating the list, so the strip stays full", () => {
    const html = renderToStaticMarkup(createElement(BrandsMarquee));
    const track = html.slice(html.indexOf("animate-marquee"));
    const names = [...track.matchAll(/(?:\/>|">)(Kled AI|micro1|Maincode|Hedwig)<\/span>/g)].map((match) => match[1]);
    expect(names.length % 8).toBe(0);
    expect(names.length).toBeGreaterThanOrEqual(16);
    const half = names.length / 2;
    expect(names.slice(0, half)).toEqual(names.slice(half));
  });

  it("is free of the invented names everywhere in the site's code", () => {
    const files: string[] = [];
    const walk = (dir: string) => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const path = join(dir, entry.name);
        if (entry.isDirectory()) walk(path);
        else if (/\.(tsx?|css)$/.test(entry.name)) files.push(path);
      }
    };
    walk(join(process.cwd(), "src/components/marketing"));
    walk(join(process.cwd(), "src/app/(marketing)"));
    files.push(join(process.cwd(), "src/lib/marketing-content.ts"));
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      for (const name of INVENTED_BRANDS) expect(source.includes(name), `${name} in ${file}`).toBe(false);
    }
  });
});

describe("launch posts are captioned as real, not as examples", () => {
  it("has no Example or Sample label in any hero", () => {
    const text = textOf(renderToStaticMarkup(createElement(HomeHero)));
    expect(text).not.toMatch(/\b(example|sample)\b/i);
    // The Drop hero's first slide shows Kled's post, linked with a plain caption.
    expect(text).toContain("Kled AI’s post on X");
  });

  it("has no Example or Sample label in the proof section", () => {
    const text = textOf(renderToStaticMarkup(createElement(ProofSection)));
    expect(text).not.toMatch(/\b(example|sample)\b/i);
  });
});
