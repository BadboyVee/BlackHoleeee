import { bareXHandle } from "@/lib/creators/display";

/**
 * The founder of AGI 2027, shown in the "Meet the founder" section on the
 * home page (src/components/marketing/sections/founder.tsx).
 *
 * Set `founder` to null to hide the section: nothing renders, no heading, no
 * empty card. Real details only. Never put sample or made up details here,
 * because whatever is set here goes live.
 */
export type Founder = {
  /** Full name, as it should read in the heading. Initials come from it when there's no photo. */
  name: string;
  /** Title or role, shown under the name (for example the job title). */
  role: string;
  /**
   * A portrait. Put the image in public/ (a square or 4:5 .webp works best)
   * and give its path from the site root, like "/founder/portrait.webp".
   * `alt` describes the photo for screen readers. Null shows initials instead.
   */
  photo: { src: string; alt: string } | null;
  /** X handle, with or without the @. Null hides the "Follow on X" link. */
  xHandle: string | null;
  /** One to three short paragraphs, in the site's voice: short sentences, no dashes. */
  bio: string[];
  /** A short line in the founder's own words, shown as a pull quote. Null hides it. */
  quote: string | null;
};

/**
 * Sent by the owner on 17 Oct 2026: their X profile and its picture. X blocks
 * this server, so the name is their handle until they send the name they want
 * shown. The bio only restates what the site already says about the agency;
 * the owner chose to keep it as written (18 Oct 2026).
 */
export const founder: Founder | null = {
  name: "Vikktorrrre",
  role: "Founder",
  photo: {
    src: "/founder/portrait.webp",
    alt: "The founder's profile picture: an illustrated portrait with dark hair, glasses and a green scarf.",
  },
  xHandle: "vikktorrrre",
  bio: ["Started AGI 2027 to get AI and tech launches seen by the people who'd actually use them."],
  quote: null,
};

/** The founder's X handle without the @, or null when there isn't one (or no founder). */
export function founderXHandle(person: Founder | null): string | null {
  return bareXHandle(person?.xHandle ?? "") || null;
}
