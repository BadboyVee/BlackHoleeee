import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { parseXPostUrl } from "@/lib/campaigns/claims";
import {
  byViews,
  excerptPost,
  getShowcasePost,
  mediaAspect,
  postIdTime,
  showcasePosts,
  splitPostText,
  statNumber,
  statsDates,
} from "@/lib/showcase-posts";

const PUBLIC = join(__dirname, "../../public");

/** Width and height of a lossy or lossless WebP, read from its header. */
function webpSize(path: string) {
  const b = readFileSync(path);
  expect(b.toString("ascii", 0, 4)).toBe("RIFF");
  expect(b.toString("ascii", 8, 12)).toBe("WEBP");
  const chunk = b.toString("ascii", 12, 16);
  if (chunk === "VP8 ") return { width: b.readUInt16LE(26) & 0x3fff, height: b.readUInt16LE(28) & 0x3fff };
  if (chunk === "VP8L") {
    const bits = b.readUInt32LE(21);
    return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 };
  }
  if (chunk === "VP8X") return { width: b.readUIntLE(24, 3) + 1, height: b.readUIntLE(27, 3) + 1 };
  throw new Error(`Unknown WebP chunk ${chunk}`);
}

describe("showcase posts", () => {
  it("has the six posts the owner sent, each once", () => {
    expect(showcasePosts).toHaveLength(6);
    expect(new Set(showcasePosts.map((post) => post.id)).size).toBe(6);
  });

  it.each(showcasePosts.map((post) => [post.author.name, post] as const))(
    "%s: the link points at the same post and author",
    (_, post) => {
      const ref = parseXPostUrl(post.url);
      expect(ref).toEqual({ handle: post.author.handle, postId: post.id });
    },
  );

  it.each(showcasePosts.map((post) => [post.author.name, post] as const))(
    "%s: the date is the one encoded in the post ID",
    (_, post) => {
      const fromId = postIdTime(post.id);
      expect(Math.abs(fromId.getTime() - new Date(post.postedAt).getTime())).toBeLessThan(1000);
      expect(fromId.getTime()).toBeLessThan(new Date(`${post.statsAsOf}T23:59:59Z`).getTime());
    },
  );

  it.each(showcasePosts.map((post) => [post.author.name, post] as const))(
    "%s: the pictures exist, at the size the page reserves",
    (_, post) => {
      expect(statSync(join(PUBLIC, post.author.avatar)).size).toBeGreaterThan(0);
      expect(webpSize(join(PUBLIC, post.media.src))).toEqual({ width: post.media.width, height: post.media.height });
      expect(post.media.alt.length).toBeGreaterThan(20);
    },
  );

  it("shows numbers only in X's own format", () => {
    for (const post of showcasePosts) {
      for (const value of Object.values(post.stats)) expect(value).toMatch(/^\d{1,3}(\.\d)?[KM]?$/);
    }
  });

  it("dates each post's numbers to its own screenshot, never before the post", () => {
    expect(statsDates(showcasePosts)).toEqual({ from: "2026-10-12", to: "2026-10-22" });
    expect(statsDates([getShowcasePost("2105311618284527767")])).toEqual({ from: "2026-10-12", to: "2026-10-12" });
    for (const post of showcasePosts) expect(post.statsAsOf >= post.postedAt.slice(0, 10)).toBe(true);
  });

  it("keeps micro1's Medical Index post as the owner sent it", () => {
    const post = getShowcasePost("2112985194529767489");
    expect(post.author).toMatchObject({ name: "micro1", handle: "micro1_ai", avatarShape: "square", badge: "gold" });
    expect(post.brand).toBe("micro1");
    expect(post.text.startsWith("Today we’re announcing the micro1 Medical Index")).toBe(true);
    expect(post.text.endsWith("Full reports linked in the comments below!")).toBe(true);
    expect(post.text.split("\n\n")).toHaveLength(7);
    expect(post.stats).toEqual({ views: "112K", replies: "33", reposts: "46", likes: "229", bookmarks: "56" });
    expect(post.statsAsOf).toBe("2026-10-22");
  });

  it("finds a post by ID and refuses an unknown one", () => {
    expect(getShowcasePost("2105311618284527767").author.handle).toBe("useKled");
    expect(() => getShowcasePost("1")).toThrow();
  });
});

describe("postIdTime", () => {
  it("decodes X's snowflake IDs", () => {
    expect(postIdTime("2105311618284527767").toISOString()).toBe("2026-09-30T14:59:39.254Z");
  });
});

describe("splitPostText", () => {
  it("marks mentions, hashtags and the given links", () => {
    expect(splitPostText("Built on @AMD MI355X #Nebula2, see hedwigmail.com.", ["hedwigmail.com"])).toEqual([
      { kind: "text", text: "Built on " },
      { kind: "mention", text: "@AMD" },
      { kind: "text", text: " MI355X " },
      { kind: "hashtag", text: "#Nebula2" },
      { kind: "text", text: ", see " },
      { kind: "link", text: "hedwigmail.com" },
      { kind: "text", text: "." },
    ]);
  });

  it("leaves emails and mid-word symbols alone", () => {
    expect(splitPostText("mail me@site.com or a#b")).toEqual([{ kind: "text", text: "mail me@site.com or a#b" }]);
  });

  it("keeps the text intact when put back together", () => {
    for (const post of showcasePosts) {
      expect(splitPostText(post.text, post.links).map((part) => part.text).join("")).toBe(post.text);
    }
  });
});

describe("excerptPost", () => {
  it("returns short text unchanged", () => {
    expect(excerptPost("Short post.", 40)).toEqual({ text: "Short post.", cut: false });
  });

  it("cuts long text at a word boundary and adds an ellipsis", () => {
    const { text, cut } = excerptPost("Today we are open-sourcing Matilda Jev, Australia’s first decision model", 40);
    expect(cut).toBe(true);
    expect(text).toBe("Today we are open-sourcing Matilda Jev…");
  });
});

describe("statNumber and byViews", () => {
  it("reads X's short counts", () => {
    expect(statNumber("3.7M")).toBe(3_700_000);
    expect(statNumber("456K")).toBe(456_000);
    expect(statNumber("769")).toBe(769);
    expect(statNumber(undefined)).toBe(-1);
  });

  it("puts the most viewed first and unknown views last", () => {
    expect(byViews(showcasePosts).map((post) => post.stats.views ?? "none")).toEqual([
      "3.7M",
      "1.8M",
      "456K",
      "171K",
      "112K",
      "none",
    ]);
  });
});

describe("mediaAspect", () => {
  it("keeps wide pictures whole and crops tall ones to 16:10", () => {
    const media = getShowcasePost("2108613100413096046").media;
    expect(mediaAspect(media)).toBe("800 / 416");
    expect(mediaAspect(getShowcasePost("2105230308132225289").media)).toBe("16 / 10");
  });
});
