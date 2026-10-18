import { readFileSync } from "node:fs";
import { createElement, type ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import {
  CLAIM_PREVIEW,
  CLAIM_PREVIEW_LABEL,
  ClaimPreview,
  KLED_LAUNCH_AT,
} from "@/components/marketing/sections/claim-preview";
import { ForCreatorsSection } from "@/components/marketing/sections/for-creators";
import { GUIDE_PREVIEW_LABEL, GUIDE_STEPS, GuidePreview } from "@/components/marketing/sections/guide-preview";
import { getShowcasePost } from "@/lib/showcase-posts";

// React hoists a preload <link> for each eager image; the phone starts after it.
const render = (component: (props: { className?: string }) => ReactNode) =>
  renderToStaticMarkup(createElement(component)).replace(/^(<link [^>]*\/>)+/, "");
const claimHtml = render(ClaimPreview);
const guideHtml = render(GuidePreview);
const kled = getShowcasePost("2105311618284527767");

/** The visible words, without tags or attributes. */
const textOf = (html: string) =>
  html
    .replace(/<[^>]+>/g, " ")
    .replace(/&#x27;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ");

/** What a screen reader hears for the phone. */
const labelOf = (html: string) => html.match(/aria-label="([^"]*)"/)?.[1] ?? "";

describe("ClaimPreview, the campaign phone", () => {
  it("greets Jesse with Kled's real V3 launch", () => {
    const text = textOf(claimHtml);
    expect(text).toContain("Good morning, Jesse");
    expect(text).toContain("Kled AI");
    expect(text).toContain("Kled V3 launch day");
    expect(CLAIM_PREVIEW.brand).toBe(kled.author.name);
  });

  it("shows Kled's own picture and video still, not a letter tile", () => {
    expect(claimHtml).toContain(`src="${kled.author.avatar}"`);
    expect(claimHtml).toContain(`src="${kled.media.src}"`);
    expect(textOf(claimHtml)).not.toMatch(/\bNA\b/);
  });

  it("dates the launch from the real post", () => {
    expect(kled.postedAt).toBe("2026-09-30T14:59:39Z");
    // The post went out in the minute before the 15:00 launch slot.
    const early = Date.parse(KLED_LAUNCH_AT) - Date.parse(kled.postedAt);
    expect(early).toBeGreaterThan(0);
    expect(early).toBeLessThan(60_000);
    expect(textOf(claimHtml)).toContain("Launch Wed 30 Sep, 15:00 UTC");
  });

  it("takes its angle from the post's own words", () => {
    expect(kled.text).toContain("under 72 hours");
    expect(CLAIM_PREVIEW.angle).toContain("under 72 hours");
    expect(textOf(claimHtml)).toContain(`Your angle: ${CLAIM_PREVIEW.angle}`);
  });

  it("makes up no pay, slots or the old sample names", () => {
    const said = `${textOf(claimHtml)} ${labelOf(claimHtml)}`;
    for (const madeUp of ["Nebula", "Amara", "250", "USDC 250", "Slots", "slots", "You earn", "/20", "USDC"]) {
      expect(said).not.toContain(madeUp);
    }
    expect(claimHtml).not.toContain("Nebula");
    expect(claimHtml).not.toContain("Amara");
    expect(textOf(claimHtml)).toContain("Paid per post");
  });

  it("starts on Claim, before the tap", () => {
    expect(textOf(claimHtml)).toContain("Claim");
    expect(textOf(claimHtml)).not.toContain("You're in");
  });
});

describe("GuidePreview, the how it works phone", () => {
  it("says hi to Jesse", () => {
    const text = textOf(guideHtml);
    expect(text).toContain("Hi Jesse");
    expect(text).toContain("How it works");
  });

  it("lists the steps in order, from applying to getting paid", () => {
    expect(GUIDE_STEPS.map((step) => step.title)).toEqual([
      "Apply",
      "Get approved",
      "Claim a drop",
      "Post in the window",
      "Send proof, get paid",
    ]);
    const text = textOf(guideHtml);
    let from = 0;
    for (const step of GUIDE_STEPS) {
      const at = text.indexOf(step.title, from);
      expect(at, step.title).toBeGreaterThanOrEqual(from);
      expect(text.indexOf(step.body, at)).toBeGreaterThan(at);
      from = at + step.title.length;
    }
    expect(guideHtml.match(/<li\b/g)).toHaveLength(GUIDE_STEPS.length);
  });

  it("uses the site's own words and no numbers beyond the step count", () => {
    const words = GUIDE_STEPS.map((step) => `${step.title} ${step.body}`).join(" ");
    expect(words).toContain("About five minutes");
    expect(words).toContain("Telegram");
    expect(words).toContain("paid per post");
    expect(words).not.toMatch(/\d/);
    expect(words).not.toMatch(/[\u2013\u2014]/);
  });
});

describe("both phones", () => {
  it("are one labelled picture each, with nothing to tab to", () => {
    for (const html of [claimHtml, guideHtml]) {
      expect(html).toMatch(/^<div[^>]*role="img"[^>]*aria-label="A creator&#x27;s phone: [^"]+"/);
      expect(html).not.toMatch(/<(a|button|input|select|textarea)\b/);
      expect(html).not.toContain("tabindex");
    }
  });

  it("are labelled the same way, each saying what it shows", () => {
    expect(labelOf(claimHtml).replace(/&#x27;/g, "'")).toBe(CLAIM_PREVIEW_LABEL);
    expect(labelOf(guideHtml).replace(/&#x27;/g, "'")).toBe(GUIDE_PREVIEW_LABEL);
    expect(CLAIM_PREVIEW_LABEL).toBe(
      "A creator's phone: Jesse claims the Kled V3 launch day campaign from Kled AI in one tap.",
    );
    for (const step of ["apply", "get approved", "claim a drop", "post in the window", "send proof", "get paid"]) {
      expect(GUIDE_PREVIEW_LABEL.toLowerCase()).toContain(step);
    }
    for (const label of [CLAIM_PREVIEW_LABEL, GUIDE_PREVIEW_LABEL]) {
      expect(label).toMatch(/^A creator's phone: .+\.$/);
      expect(label).not.toMatch(/[\u2013\u2014]/);
    }
  });

  it("leave no made up sample behind in their files or the preview screens", () => {
    const files = [
      "src/components/marketing/sections/phone-frame.tsx",
      "src/components/marketing/sections/claim-preview.tsx",
      "src/components/marketing/sections/guide-preview.tsx",
      "src/components/marketing/sections/for-creators.tsx",
      "src/app/(auth)/application/page.tsx",
      "src/app/(auth)/invite/[code]/page.tsx",
    ];
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      for (const madeUp of ["Nebula", "Amara", "amara", "USDC 250", "Slots"]) {
        expect(source, `${file} has ${madeUp}`).not.toContain(madeUp);
      }
      expect(source, `${file} has a long dash`).not.toMatch(/[\u2013\u2014]/);
    }
  });

  it("share the same frame", () => {
    const frame = (html: string) => html.match(/^<div[^>]*><div class="[^"]+">/)?.[0];
    expect(frame(claimHtml)).toBeDefined();
    expect(frame(claimHtml)?.replace(/aria-label="[^"]*"/, "")).toBe(frame(guideHtml)?.replace(/aria-label="[^"]*"/, ""));
  });

  it("show up together in every look of the For creators section", () => {
    const html = renderToStaticMarkup(createElement(ForCreatorsSection));
    expect(html.match(/Good morning, Jesse/g)).toHaveLength(3);
    expect(html.match(/Hi Jesse/g)).toHaveLength(3);
    expect(html).not.toContain("Nebula");
    expect(html).not.toContain("Amara");
  });
});
