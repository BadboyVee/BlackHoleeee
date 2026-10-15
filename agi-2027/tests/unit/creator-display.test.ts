import { describe, expect, it } from "vitest";

import { avatarPath, avatarPublicUrl, avatarTypeProblem, isOwnAvatarUrl } from "@/lib/creators/avatar";
import {
  formatCount,
  inviteLink,
  inviteStatusOf,
  inviteUsage,
  otherSocials,
  referralLink,
  shortLink,
  xProfileUrl,
} from "@/lib/creators/display";

describe("formatCount", () => {
  it("reads like a person would say it, rounding down", () => {
    expect(formatCount(0)).toBe("0");
    expect(formatCount(950)).toBe("950");
    expect(formatCount(1000)).toBe("1k");
    expect(formatCount(18_400)).toBe("18.4k");
    expect(formatCount(18_499)).toBe("18.4k");
    expect(formatCount(999_999)).toBe("999.9k");
    expect(formatCount(1_200_000)).toBe("1.2M");
    expect(formatCount(152_000)).toBe("152k");
  });

  it("says when there's no number", () => {
    expect(formatCount(null)).toBe("Not given");
    expect(formatCount(undefined)).toBe("Not given");
  });
});

describe("links", () => {
  it("builds referral and invite links on the site's address", () => {
    expect(referralLink("9f3a1c2b", "https://agi2027.example/")).toBe("https://agi2027.example/apply?ref=9f3a1c2b");
    expect(inviteLink("7c2e9a41d03f5b86", "https://agi2027.example")).toBe("https://agi2027.example/invite/7c2e9a41d03f5b86");
  });

  it("links to X profiles and shortens post links for display", () => {
    expect(xProfileUrl("amarabuilds")).toBe("https://x.com/amarabuilds");
    expect(xProfileUrl("@amarabuilds")).toBe("https://x.com/amarabuilds");
    expect(shortLink("https://www.x.com/a/status/1/")).toBe("x.com/a/status/1");
  });

  it("lists only the socials someone gave, in a fixed order", () => {
    expect(
      otherSocials({
        tiktokUrl: null,
        youtubeUrl: "https://youtube.com/@a",
        instagramUrl: null,
        linkedinUrl: "https://linkedin.com/in/a",
      }),
    ).toEqual([
      { platform: "youtube", label: "YouTube", url: "https://youtube.com/@a" },
      { platform: "linkedin", label: "LinkedIn", url: "https://linkedin.com/in/a" },
    ]);
  });
});

describe("invite links", () => {
  const now = new Date("2026-11-03T19:00:00Z");
  const base = { revokedAt: null, expiresAt: null, maxUses: null, uses: 0 };

  it("works out where a link stands, in the database's order", () => {
    expect(inviteStatusOf(base, now)).toBe("valid");
    expect(inviteStatusOf({ ...base, expiresAt: "2026-11-03T19:00:00Z" }, now)).toBe("expired");
    expect(inviteStatusOf({ ...base, expiresAt: "2026-11-03T19:00:01Z" }, now)).toBe("valid");
    expect(inviteStatusOf({ ...base, maxUses: 5, uses: 5 }, now)).toBe("used_up");
    expect(inviteStatusOf({ ...base, maxUses: 5, uses: 5, revokedAt: "2026-10-01T00:00:00Z" }, now)).toBe("revoked");
  });

  it("describes how much a link has been used", () => {
    expect(inviteUsage({ maxUses: 40, uses: 17 })).toBe("17 of 40 used");
    expect(inviteUsage({ maxUses: null, uses: 0 })).toBe("No uses yet");
    expect(inviteUsage({ maxUses: null, uses: 1 })).toBe("1 use");
    expect(inviteUsage({ maxUses: null, uses: 3 })).toBe("3 uses");
  });
});

describe("profile photos", () => {
  const supabase = "https://project.supabase.co/";
  const me = "8a7d5c1e-0000-4000-8000-000000000001";

  it("keeps one photo per person, in their own folder", () => {
    expect(avatarPath(me)).toBe(`${me}/avatar.webp`);
    expect(avatarPublicUrl(supabase, me, 42)).toBe(
      `https://project.supabase.co/storage/v1/object/public/avatars/${me}/avatar.webp?v=42`,
    );
  });

  it("accepts only the person's own photo address", () => {
    const own = avatarPublicUrl(supabase, me, 1760540000000);
    expect(isOwnAvatarUrl(own, supabase, me)).toBe(true);
    expect(isOwnAvatarUrl(own.replace(/\?v=\d+$/, ""), supabase, me)).toBe(true);
    expect(isOwnAvatarUrl(own.replace(me, "someone-else"), supabase, me)).toBe(false);
    expect(isOwnAvatarUrl(`${own}#x`, supabase, me)).toBe(false);
    expect(isOwnAvatarUrl(own.replace("?v=", "?w="), supabase, me)).toBe(false);
    expect(isOwnAvatarUrl("https://lh3.googleusercontent.com/a/x", supabase, me)).toBe(false);
  });

  it("explains a file it can't use", () => {
    expect(avatarTypeProblem("image/png", 1024)).toBeNull();
    expect(avatarTypeProblem("image/gif", 1024)).toBe("Pick a JPG, PNG or WebP image.");
    expect(avatarTypeProblem("image/jpeg", 11 * 1024 * 1024)).toBe("That image is over 10 MB. Pick a smaller one.");
  });
});
