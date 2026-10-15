import { siteConfig } from "@/lib/site";
import type { InviteStatus } from "@/lib/statuses";

/*
 * How creator facts read on screen: counts, links to their profiles, and the
 * addresses of referral and invite links. No Intl number formatting: ICU
 * versions differ between Node and browsers, which breaks hydration.
 */

function trimZero(value: number): string {
  return value.toFixed(1).replace(/\.0$/, "");
}

/** 950, 18.4k, 1.2M. Rounds down, so a count never reads higher than it is. */
export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not given";
  if (value < 1_000) return String(Math.max(0, Math.floor(value)));
  if (value < 1_000_000) {
    const thousands = Math.floor(value / 100) / 10;
    return thousands >= 1_000 ? "1M" : `${trimZero(thousands)}k`;
  }
  return `${trimZero(Math.floor(value / 100_000) / 10)}M`;
}

function base(siteUrl: string): string {
  return siteUrl.replace(/\/+$/, "");
}

/** The creator's personal link: /apply with their code, which the application form picks up. */
export function referralLink(code: string, siteUrl: string = siteConfig.url): string {
  return `${base(siteUrl)}/apply?ref=${code}`;
}

export function inviteLink(code: string, siteUrl: string = siteConfig.url): string {
  return `${base(siteUrl)}/invite/${code}`;
}

/** "amarabuilds" (stored without the @) to their X profile. */
export function xProfileUrl(handle: string): string {
  return `https://x.com/${handle.replace(/^@+/, "")}`;
}

export type InviteLike = { revokedAt: string | null; expiresAt: string | null; maxUses: number | null; uses: number };

/** Where an invite link stands at `now`. Mirrors private.invite_state in the database. */
export function inviteStatusOf(invite: InviteLike, now: Date): InviteStatus {
  if (invite.revokedAt) return "revoked";
  if (invite.expiresAt && new Date(invite.expiresAt).getTime() <= now.getTime()) return "expired";
  if (invite.maxUses !== null && invite.uses >= invite.maxUses) return "used_up";
  return "valid";
}

/** "3 of 10 used", "1 use" or "No uses yet". */
export function inviteUsage(invite: Pick<InviteLike, "maxUses" | "uses">): string {
  if (invite.maxUses !== null) return `${invite.uses} of ${invite.maxUses} used`;
  if (invite.uses === 0) return "No uses yet";
  return invite.uses === 1 ? "1 use" : `${invite.uses} uses`;
}

export type SocialLinks = {
  tiktokUrl: string | null;
  youtubeUrl: string | null;
  instagramUrl: string | null;
  linkedinUrl: string | null;
};

/** The other socials a creator gave, in a fixed order, for link rows. */
export function otherSocials(links: SocialLinks): { platform: "tiktok" | "youtube" | "instagram" | "linkedin"; label: string; url: string }[] {
  const all = [
    { platform: "tiktok", label: "TikTok", url: links.tiktokUrl },
    { platform: "youtube", label: "YouTube", url: links.youtubeUrl },
    { platform: "instagram", label: "Instagram", url: links.instagramUrl },
    { platform: "linkedin", label: "LinkedIn", url: links.linkedinUrl },
  ] as const;
  return all.flatMap((social) => (social.url ? [{ platform: social.platform, label: social.label, url: social.url }] : []));
}

/** "x.com/amara/status/123" from a full post link, for link text. */
export function shortLink(url: string): string {
  return url.replace(/^https?:\/\/(www\.)?/, "").replace(/\/+$/, "");
}
