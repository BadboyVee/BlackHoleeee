import { existsSync } from "node:fs";
import { join } from "node:path";

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CreatorRosterSection } from "@/components/marketing/sections/creator-roster";
import { founder, founderXHandle } from "@/lib/founder";
import {
  combinedFollowers,
  compactFollowers,
  creatorRoster,
  ROSTER_AS_OF,
  type RosterCreator,
} from "@/lib/creator-roster";

// Made up creators for this test only. Never copy them into src/lib/creator-roster.ts.
const sample: RosterCreator[] = [
  { name: "Test Person", xHandle: "test_person", followers: 980, avatar: "/test/one.webp" },
  { name: "Another Tester", xHandle: "another_tester", followers: 51_200, avatar: "/test/two.webp" },
  { name: "Third Example", xHandle: "third_example", followers: 118_000, avatar: "/test/three.webp" },
  { name: "Big Account", xHandle: "big_account", followers: 1_250_000, avatar: "/test/four.webp" },
];

const render = (creators: RosterCreator[], asOf: string | null = "2026-10-17") =>
  renderToStaticMarkup(createElement(CreatorRosterSection, { creators, asOf }));

/** Every link in the markup, with its opening tag and its text without tags. */
function links(html: string) {
  return [...html.matchAll(/(<a [^>]*>)([\s\S]*?)<\/a>/g)].map(([, tag, inner]) => ({
    tag,
    href: /href="([^"]*)"/.exec(tag)?.[1],
    srText: [...inner.matchAll(/<span class="sr-only">([^<]*)<\/span>/g)].map((match) => match[1]).join(""),
  }));
}

describe("creatorRoster (the live list)", () => {
  it("has the owner's 14 creators, in the owner's order, with the counts X showed on 17 Oct 2026", () => {
    expect(creatorRoster.map((creator) => [creator.name, creator.xHandle, creator.followers])).toEqual([
      ["Pain", "painn_x", 9_560],
      ["m0h", "exploraX_", 26_300],
      ["Khushi", "khushiirl", 15_100],
      ["Aditi", "aditiitwt", 16_600],
      ["Foxy", "badboyfoxy", 3_598],
      ["Haleemah", "Haleeeemahh", 6_237],
      ["MystiqueMide", "MystiqueMide", 5_119],
      ["Alan", "alannnfx", 9_059],
      ["Agim", "aGim_asf", 6_944],
      ["Sakata", "sakatayasha", 9_104],
      ["Marcel", "marcthecreatorr", 2_653],
      ["Breeze", "BreezeOg1", 2_586],
      ["Vorpal", "vorpal_onchain", 3_700],
      ["Jazii", "notjazii", 12_100],
    ]);
    expect(ROSTER_AS_OF).toBe("2026-10-17");
    expect(combinedFollowers(creatorRoster)).toBe(128_660);
  });

  it("gives every creator their own picture, named after their handle in lower case", () => {
    expect(creatorRoster).toHaveLength(14);
    for (const creator of creatorRoster) {
      expect(creator.avatar).toBe(`/creators/${creator.xHandle.toLowerCase()}.webp`);
      expect(existsSync(join(process.cwd(), "public", creator.avatar)), `missing ${creator.avatar}`).toBe(true);
    }
    expect(new Set(creatorRoster.map((creator) => creator.avatar)).size).toBe(14);
  });

  it("is a list, and each creator's picture is in public/ with a handle without the @", () => {
    expect(Array.isArray(creatorRoster)).toBe(true);
    for (const creator of creatorRoster) {
      expect(creator.name.trim()).not.toBe("");
      expect(creator.xHandle).toMatch(/^[A-Za-z0-9_]{1,15}$/);
      expect(Number.isInteger(creator.followers) && creator.followers >= 0).toBe(true);
      expect(creator.avatar).toMatch(/^\/creators\/.+\.webp$/);
      expect(existsSync(join(process.cwd(), "public", creator.avatar)), `missing ${creator.avatar}`).toBe(true);
    }
  });

  it("lists each creator once", () => {
    const handles = creatorRoster.map((creator) => creator.xHandle.toLowerCase());
    expect(new Set(handles).size).toBe(handles.length);
  });

  it("says which day the counts are from once there are creators", () => {
    if (ROSTER_AS_OF !== null) {
      expect(ROSTER_AS_OF).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(Number.isNaN(new Date(ROSTER_AS_OF).getTime())).toBe(false);
    }
    if (creatorRoster.length > 0) expect(ROSTER_AS_OF).not.toBeNull();
  });
});

describe("compactFollowers", () => {
  it("reads like X, rounding down so a count never reads higher than it is", () => {
    expect(compactFollowers(980)).toBe("980");
    expect(compactFollowers(1_000)).toBe("1K");
    expect(compactFollowers(51_200)).toBe("51.2K");
    expect(compactFollowers(51_299)).toBe("51.2K");
    expect(compactFollowers(118_000)).toBe("118K");
    expect(compactFollowers(1_250_000)).toBe("1.2M");
  });

  it("adds everyone up", () => {
    expect(combinedFollowers(sample)).toBe(980 + 51_200 + 118_000 + 1_250_000);
    expect(combinedFollowers([])).toBe(0);
  });
});

describe("CreatorRosterSection", () => {
  it("renders nothing while there are no creators", () => {
    expect(render([])).toBe("");
    expect(render([], null)).toBe("");
  });

  it("renders the live list on the home page, or nothing while it's empty", () => {
    const html = render(creatorRoster, ROSTER_AS_OF);
    if (creatorRoster.length === 0) expect(html).toBe("");
    else expect(links(html)).toHaveLength(creatorRoster.length);
  });

  it("has a heading that names the section", () => {
    const html = render(sample);
    expect(html).toContain('id="roster"');
    expect(html).toContain('aria-labelledby="roster-heading"');
    expect(html).toContain('id="roster-heading"');
    expect(html).toMatch(/<h2[^>]*aria-label="The creators behind the launches."/);
  });

  it("shows each creator's picture, name, handle and followers, in the listed order", () => {
    const html = render(sample);
    for (const creator of sample) {
      expect(html).toContain(`>${creator.name}<`);
      expect(html).toContain(`>@${creator.xHandle}<`);
      expect(html).toContain(encodeURIComponent(creator.avatar));
    }
    expect(html).toMatch(/>980<\/span><span[^>]*>followers</);
    expect(html).toMatch(/>51\.2K<\/span><span[^>]*>followers</);
    expect(html).toMatch(/>118K<\/span><span[^>]*>followers</);
    expect(html).toMatch(/>1\.2M<\/span><span[^>]*>followers</);
    const order = sample.map((creator) => html.indexOf(`>@${creator.xHandle}<`));
    expect(order).toEqual([...order].sort((a, b) => a - b));
  });

  it("links each whole card to the creator on X, in a new tab", () => {
    const cards = links(render(sample));
    expect(cards).toHaveLength(sample.length);
    cards.forEach((card, index) => {
      const creator = sample[index];
      expect(card.href).toBe(`https://x.com/${creator.xHandle}`);
      expect(card.tag).toContain('target="_blank"');
      expect(card.tag).toContain('rel="noopener noreferrer"');
    });
    expect(cards[1].srText).toBe("Another Tester, @another_tester on X, 51.2K followers (opens in a new tab)");
    expect(cards[3].srText).toBe("Big Account, @big_account on X, 1.2M followers (opens in a new tab)");
  });

  it("leaves the @ out of the address even if a handle has one", () => {
    const [card] = links(render([{ ...sample[0], xHandle: "@test_person" }]));
    expect(card.href).toBe("https://x.com/test_person");
    expect(card.srText).toBe("Test Person, @test_person on X, 980 followers (opens in a new tab)");
  });

  it("says follower, not followers, for one", () => {
    const [card] = links(render([{ ...sample[0], followers: 1 }]));
    expect(card.srText).toBe("Test Person, @test_person on X, 1 follower (opens in a new tab)");
  });

  it("adds up everyone's followers, rounding down", () => {
    // 1,420,180 in all.
    expect(render(sample)).toMatch(/>1\.4M<\/span> <span[^>]*>followers between them</);
  });

  it("shows no tiers, badges or labels", () => {
    const text = render(sample).replace(/<[^>]+>/g, " ").toLowerCase();
    for (const word of ["premium", "tier", "elite", "gold", "silver", "bronze", "verified", "badge", "vip", "rank", "top creator", "mega", "macro", "micro", "nano"]) {
      expect(text).not.toMatch(new RegExp(`\\b${word}\\b`));
    }
  });

  it("asks creators who aren't listed to message the founder on X, in a new tab", () => {
    const handle = founderXHandle(founder);
    expect(handle).toBe("vikktorrrre");
    const html = renderToStaticMarkup(
      createElement(CreatorRosterSection, { creators: sample, asOf: "2026-10-17", contactXHandle: handle }),
    );
    expect(html.replace(/<[^>]+>/g, "")).toContain("One of our creators and not on here? Message us on X");
    const all = links(html);
    expect(all).toHaveLength(sample.length + 1);
    const note = all[all.length - 1];
    expect(note.href).toBe("https://x.com/vikktorrrre");
    expect(note.tag).toContain('target="_blank"');
    expect(note.tag).toContain('rel="noopener noreferrer"');
    expect(note.srText).toBe(" (opens in a new tab)");
  });

  it("leaves the @ out of the founder's address too", () => {
    const html = renderToStaticMarkup(
      createElement(CreatorRosterSection, { creators: sample, asOf: null, contactXHandle: " @someone " }),
    );
    expect(links(html).at(-1)?.href).toBe("https://x.com/someone");
  });

  it("leaves the note out when there's no handle to message", () => {
    expect(founderXHandle(null)).toBeNull();
    if (founder) expect(founderXHandle({ ...founder, xHandle: null })).toBeNull();
    for (const contactXHandle of [null, undefined, "", "  ", "@"]) {
      const html = renderToStaticMarkup(createElement(CreatorRosterSection, { creators: sample, asOf: null, contactXHandle }));
      expect(html).not.toContain("not on here");
      expect(links(html)).toHaveLength(sample.length);
    }
  });

  it("says which day the counts are from, when it's set", () => {
    expect(render(sample, "2026-10-17")).toContain("Follower counts as X showed them on 17 Oct 2026.");
    expect(render(sample, null)).not.toContain("Follower counts as");
  });
});
