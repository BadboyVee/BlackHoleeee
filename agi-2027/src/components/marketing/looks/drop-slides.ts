/**
 * The Drop hero's slides: one word for each kind of attention we sell, a real
 * launch post on X standing in front of it (see src/lib/showcase-posts.ts),
 * and the floating icons around it.
 */

export type DropIcon = {
  name: "heart" | "bubble" | "hash" | "badge" | "bolt" | "spark" | "arrow" | "bars" | "sparklime" | "heartwhite";
  /** Position of the icon's centre, in % of the hero. */
  x: number;
  y: number;
  /** Width in vmin units. */
  size: number;
  rotate: number;
  /** 0 is far (small parallax), 1 is near (blurred, more parallax). */
  depth: number;
  /** Hidden on phones to keep the screen calm. */
  desktopOnly?: boolean;
  /** Where it sits on phones, if not the same place. */
  phone?: { x: number; y: number };
};

export type DropSlide = {
  id: string;
  word: string;
  color: string;
  /** A darker shade for shadows and the vignette. */
  shade: string;
  title: string;
  body: string;
  /** The real post the phone shows, from showcasePosts. */
  postId: string;
  icons: DropIcon[];
};

export const dropSlides: DropSlide[] = [
  {
    id: "launch",
    word: "Launch",
    color: "#e0252b",
    shade: "#9e1015",
    title: "Launch campaigns",
    body: "A wave of creators, one launch day, every post timed to the minute.",
    postId: "2105311618284527767",
    icons: [
      { name: "bolt", x: 15, y: 27, size: 9, rotate: -14, depth: 0.35 },
      { name: "heartwhite", x: 80, y: 30, size: 11, rotate: 12, depth: 0.5 },
      { name: "bubble", x: 72, y: 74, size: 10, rotate: -8, depth: 0.4, desktopOnly: true },
      { name: "spark", x: 30, y: 78, size: 7, rotate: 18, depth: 0.25, phone: { x: 18, y: 58 } },
      { name: "badge", x: 93, y: 88, size: 17, rotate: -10, depth: 1, desktopOnly: true },
    ],
  },
  {
    id: "funding",
    word: "Funding",
    color: "#1e6bff",
    shade: "#0b3aa8",
    title: "Funding news",
    body: "Your raise, explained by the people founders already listen to.",
    postId: "2108613100413096046",
    icons: [
      { name: "arrow", x: 17, y: 30, size: 9, rotate: 6, depth: 0.4 },
      { name: "sparklime", x: 82, y: 26, size: 8, rotate: -16, depth: 0.3 },
      { name: "bars", x: 76, y: 72, size: 10, rotate: 8, depth: 0.45, desktopOnly: true },
      { name: "heart", x: 27, y: 76, size: 9, rotate: -12, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "bolt", x: 6, y: 86, size: 16, rotate: 22, depth: 1, desktopOnly: true },
    ],
  },
  {
    id: "drop",
    word: "Drop",
    color: "#cf4a00",
    shade: "#8a2f00",
    title: "Product drops",
    body: "Creators show it working, on the day it ships, in their own words.",
    postId: "2105230308132225289",
    icons: [
      { name: "heartwhite", x: 16, y: 25, size: 10, rotate: -18, depth: 0.45 },
      { name: "bubble", x: 84, y: 30, size: 10, rotate: 10, depth: 0.4 },
      { name: "spark", x: 74, y: 77, size: 7, rotate: -6, depth: 0.25, desktopOnly: true },
      { name: "hash", x: 26, y: 74, size: 9, rotate: 14, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "badge", x: 94, y: 12, size: 15, rotate: 18, depth: 1, desktopOnly: true },
    ],
  },
  {
    id: "founder",
    word: "Founder",
    color: "#5b2ee8",
    shade: "#2f1494",
    title: "Founder content",
    body: "Your founder's story, carried further by voices people trust.",
    postId: "2107497652871155953",
    icons: [
      { name: "sparklime", x: 15, y: 28, size: 8, rotate: 10, depth: 0.3 },
      { name: "heart", x: 81, y: 27, size: 10, rotate: 14, depth: 0.45 },
      { name: "hash", x: 75, y: 76, size: 9, rotate: -10, depth: 0.4, desktopOnly: true },
      { name: "bubble", x: 26, y: 78, size: 9, rotate: -14, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "spark", x: 5, y: 10, size: 14, rotate: 24, depth: 1, desktopOnly: true },
    ],
  },
  {
    id: "hype",
    word: "Hype",
    color: "#127a36",
    shade: "#09461e",
    title: "Hype that converts",
    body: "Comment, repost, get access: launch posts that turn a feed into a waitlist.",
    postId: "2106449214536605976",
    icons: [
      { name: "bars", x: 16, y: 28, size: 9, rotate: -8, depth: 0.4 },
      { name: "heartwhite", x: 83, y: 29, size: 10, rotate: 10, depth: 0.45 },
      { name: "arrow", x: 74, y: 75, size: 8, rotate: 4, depth: 0.3, desktopOnly: true },
      { name: "bolt", x: 27, y: 77, size: 8, rotate: -20, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "heart", x: 95, y: 90, size: 16, rotate: -16, depth: 1, desktopOnly: true },
    ],
  },
];
