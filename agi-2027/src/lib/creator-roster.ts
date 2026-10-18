import { formatCount } from "@/lib/creators/display";

/**
 * The creators in the grid on the home page, "The creators behind the
 * launches" (src/components/marketing/sections/creator-roster.tsx). Each card
 * shows the creator's profile picture, name, X handle and follower count, and
 * links to their profile on X. No tiers or labels.
 *
 * Real creators only, as the owner sends them. Never put sample or made up
 * creators here, because whatever is in this list goes live. While the list
 * is empty the section doesn't render at all: no heading, no empty card.
 *
 * To add a creator:
 * 1. Save their X profile picture in public/creators/ as a square .webp named
 *    after their handle, like public/creators/khushiirl.webp. 320 to 400
 *    pixels across is plenty (the cards show it at 96 pixels at most).
 * 2. Add them to `creatorRoster` below: their name as it should read, their X
 *    handle without the @, their follower count as a whole number (51200, not
 *    "51.2K"), and the picture's path from the site root
 *    ("/creators/khushiirl.webp").
 * 3. Set ROSTER_AS_OF to the day the follower counts were taken.
 *
 * The grid shows creators in the order they're listed here, so put them in
 * the order the owner wants. A unit test (tests/unit/creator-roster.test.ts)
 * fails if a picture is missing from public/ or a handle has an @ in it.
 */
export type RosterCreator = {
  /** Their name as it should read on the card. */
  name: string;
  /** X handle without the @, like "khushiirl". */
  xHandle: string;
  /** Followers on X, as a whole number, on the day in ROSTER_AS_OF. */
  followers: number;
  /** Profile picture in public/, from the site root: "/creators/<handle>.webp". */
  avatar: string;
};

/**
 * The day the follower counts were taken, as "YYYY-MM-DD" (counts change, so
 * the site says when they're from). Null while there are no creators.
 */
export const ROSTER_AS_OF: string | null = "2026-10-17";

/**
 * In display order. Real creators only: see the note at the top of this file.
 *
 * Sent by the owner on 17 Oct 2026, in the owner's order. The follower counts
 * were read from the owner's screenshots of each X profile, taken that day.
 * X rounds counts over 10K ("26.3K"), so those are stored as X showed them.
 */
export const creatorRoster: RosterCreator[] = [
  { name: "Pain", xHandle: "painn_x", followers: 9_560, avatar: "/creators/painn_x.webp" },
  { name: "m0h", xHandle: "exploraX_", followers: 26_300, avatar: "/creators/explorax_.webp" },
  { name: "Khushi", xHandle: "khushiirl", followers: 15_100, avatar: "/creators/khushiirl.webp" },
  { name: "Aditi", xHandle: "aditiitwt", followers: 16_600, avatar: "/creators/aditiitwt.webp" },
  { name: "Foxy", xHandle: "badboyfoxy", followers: 3_598, avatar: "/creators/badboyfoxy.webp" },
  { name: "Haleemah", xHandle: "Haleeeemahh", followers: 6_237, avatar: "/creators/haleeeemahh.webp" },
  { name: "MystiqueMide", xHandle: "MystiqueMide", followers: 5_119, avatar: "/creators/mystiquemide.webp" },
  { name: "Alan", xHandle: "alannnfx", followers: 9_059, avatar: "/creators/alannnfx.webp" },
  { name: "Agim", xHandle: "aGim_asf", followers: 6_944, avatar: "/creators/agim_asf.webp" },
  { name: "Sakata", xHandle: "sakatayasha", followers: 9_104, avatar: "/creators/sakatayasha.webp" },
  { name: "Marcel", xHandle: "marcthecreatorr", followers: 2_653, avatar: "/creators/marcthecreatorr.webp" },
  { name: "Breeze", xHandle: "BreezeOg1", followers: 2_586, avatar: "/creators/breezeog1.webp" },
  { name: "Vorpal", xHandle: "vorpal_onchain", followers: 3_700, avatar: "/creators/vorpal_onchain.webp" },
  { name: "Jazii", xHandle: "notjazii", followers: 12_100, avatar: "/creators/notjazii.webp" },
];

/**
 * A follower count the way X shows it: 980, 51.2K, 1.2M. Rounded down, so a
 * count never reads higher than it is, and built without Intl so the server
 * and browsers always agree.
 */
export function compactFollowers(count: number): string {
  // formatCount writes "51.2k"; X and the rest of the home page write "51.2K".
  return formatCount(count).toUpperCase();
}

/** Everyone's followers added up, for the "between them" line. */
export function combinedFollowers(creators: RosterCreator[]): number {
  return creators.reduce((sum, creator) => sum + creator.followers, 0);
}
