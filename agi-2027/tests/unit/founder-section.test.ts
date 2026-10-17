import { existsSync } from "node:fs";
import { join } from "node:path";

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FounderSection } from "@/components/marketing/sections/founder";
import { founder as liveFounder, type Founder } from "@/lib/founder";

// A made up founder for this test only. Never copy it into src/lib/founder.ts.
const sample: Founder = {
  name: "Test Person",
  role: "Founder, Example Agency",
  photo: null,
  xHandle: "@test_handle",
  bio: ["First paragraph of the bio.", "Second paragraph of the bio."],
  quote: "A short line in their own words.",
};

const render = (founder: Founder | null) => renderToStaticMarkup(createElement(FounderSection, { founder }));

describe("FounderSection", () => {
  it("renders nothing until the founder is filled in", () => {
    expect(render(null)).toBe("");
  });

  it("shows the owner's real details, with a photo that's in public/", () => {
    expect(liveFounder).not.toBeNull();
    const html = render(liveFounder);
    expect(html).toContain('href="https://x.com/vikktorrrre"');
    if (liveFounder?.photo) {
      expect(liveFounder.photo.src).toMatch(/^\//);
      expect(existsSync(join(process.cwd(), "public", liveFounder.photo.src))).toBe(true);
      expect(liveFounder.photo.alt.trim()).not.toBe("");
    }
  });

  it("shows the name as the section heading, then the role, bio and quote", () => {
    const html = render(sample);
    expect(html).toContain('id="founder"');
    expect(html).toContain('aria-labelledby="founder-heading"');
    expect(html).toContain('id="founder-heading"');
    expect(html).toMatch(/<h2[^>]*aria-label="Test Person"/);
    expect(html).toContain("Meet the founder");
    expect(html).toContain("Founder, Example Agency");
    expect(html).toContain("First paragraph of the bio.");
    expect(html).toContain("Second paragraph of the bio.");
    expect(html).toMatch(/<blockquote[^>]*><p>“A short line in their own words.”<\/p><\/blockquote>/);
  });

  it("links to X in a new tab, without the @ in the address", () => {
    const html = render(sample);
    const link = html.match(/<a [^>]*href="https:\/\/x\.com\/test_handle"[^>]*>/)?.[0];
    expect(link).toBeDefined();
    expect(link).toContain('target="_blank"');
    expect(link).toContain('rel="noopener noreferrer"');
    expect(html).toContain("Follow @test_handle on X");
  });

  it("shows initials when there's no photo", () => {
    const html = render(sample);
    expect(html).toMatch(/<div aria-hidden="true" data-founder-initials="true"[^>]*><span[^>]*>TP<\/span><\/div>/);
    // The portrait is the only full bleed image in the section.
    expect(html).not.toContain('data-nimg="fill"');
  });

  it("shows the photo with its alt text when there is one", () => {
    const html = render({ ...sample, photo: { src: "/test/portrait.webp", alt: "A test portrait" } });
    expect(html).toMatch(/<img alt="A test portrait"[^>]*data-nimg="fill"/);
    expect(html).toContain("portrait.webp");
    expect(html).not.toContain("data-founder-initials");
  });

  it("leaves out the quote and the X link when they're not set", () => {
    const html = render({ ...sample, quote: null, xHandle: null });
    expect(html).not.toContain("<blockquote");
    expect(html).not.toContain("x.com");
  });
});
