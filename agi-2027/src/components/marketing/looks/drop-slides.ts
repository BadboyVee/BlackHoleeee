/**
 * The Drop hero's slides: one word for each kind of attention we sell, the
 * post a creator might write, and the floating icons around it. Brands and
 * creators are made up; numbers are sample data.
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
  post: {
    name: string;
    handle: string;
    initials: string;
    avatar: string;
    text: string;
    card: { label: string; from: string; to: string };
    time: string;
    views: string;
    stats: { replies: string; reposts: string; likes: string; saves: string };
  };
  icons: DropIcon[];
};

export const dropSlides: DropSlide[] = [
  {
    id: "launch",
    word: "Launch",
    color: "#e0252b",
    shade: "#9e1015",
    title: "Launch campaigns",
    body: "Twenty creators, one launch day, every post timed to the minute.",
    post: {
      name: "Amara Okafor",
      handle: "@amarabuilds",
      initials: "AO",
      avatar: "linear-gradient(135deg,#ffb36b,#ff5e7e)",
      text: "Built a working agent with @nebula_ai 2.0 in ten minutes. No code. This changes who gets to build. #Nebula2",
      card: { label: "Nebula 2.0", from: "#5b2ee8", to: "#9a6bff" },
      time: "4:12 PM",
      views: "412K",
      stats: { replies: "182", reposts: "1.4K", likes: "9.8K", saves: "2.1K" },
    },
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
    post: {
      name: "Lucía Ferrer",
      handle: "@luciaferrer",
      initials: "LF",
      avatar: "linear-gradient(135deg,#7ad7ff,#4a6bff)",
      text: "Search that understands meaning just got funded. Big week for @vectorline and for anyone building AI search.",
      card: { label: "Series A", from: "#0f172a", to: "#1e6bff" },
      time: "9:03 AM",
      views: "268K",
      stats: { replies: "96", reposts: "812", likes: "5.2K", saves: "1.3K" },
    },
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
    post: {
      name: "Theo Lindqvist",
      handle: "@theoships",
      initials: "TL",
      avatar: "linear-gradient(135deg,#ffe066,#ff8a3d)",
      text: "The new @lumenlabs 8B runs on my laptop. Offline, fast, open weights. Clip below, judge for yourself. #LumenOpen",
      card: { label: "Open weights", from: "#16120f", to: "#cf4a00" },
      time: "6:40 PM",
      views: "533K",
      stats: { replies: "240", reposts: "2.2K", likes: "14K", saves: "3.8K" },
    },
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
    post: {
      name: "Hana Sato",
      handle: "@hanaonai",
      initials: "HS",
      avatar: "linear-gradient(135deg,#ff9bd2,#9a6bff)",
      text: "Year one of @quillwire, told by the founder. The part about shipping docs nobody reads hit home. Worth the read.",
      card: { label: "Year one", from: "#2f1494", to: "#ff9bd2" },
      time: "11:26 AM",
      views: "187K",
      stats: { replies: "71", reposts: "604", likes: "4.1K", saves: "988" },
    },
    icons: [
      { name: "sparklime", x: 15, y: 28, size: 8, rotate: 10, depth: 0.3 },
      { name: "heart", x: 81, y: 27, size: 10, rotate: 14, depth: 0.45 },
      { name: "hash", x: 75, y: 76, size: 9, rotate: -10, depth: 0.4, desktopOnly: true },
      { name: "bubble", x: 26, y: 78, size: 9, rotate: -14, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "spark", x: 5, y: 10, size: 14, rotate: 24, depth: 1, desktopOnly: true },
    ],
  },
  {
    id: "daily",
    word: "Daily",
    color: "#127a36",
    shade: "#09461e",
    title: "Always-on posting",
    body: "A steady drumbeat of posts every month, so your name stays in the feed.",
    post: {
      name: "Priya Raman",
      handle: "@priyaprompts",
      initials: "PR",
      avatar: "linear-gradient(135deg,#b6f23a,#2ec27e)",
      text: "Week four with @orbitar and I sketch every feature on paper first now. Napkin to prototype before lunch. #OrbitarBeta",
      card: { label: "Week four", from: "#0d2b18", to: "#2ec27e" },
      time: "2:15 PM",
      views: "144K",
      stats: { replies: "58", reposts: "397", likes: "3.3K", saves: "740" },
    },
    icons: [
      { name: "bars", x: 16, y: 28, size: 9, rotate: -8, depth: 0.4 },
      { name: "heartwhite", x: 83, y: 29, size: 10, rotate: 10, depth: 0.45 },
      { name: "arrow", x: 74, y: 75, size: 8, rotate: 4, depth: 0.3, desktopOnly: true },
      { name: "bolt", x: 27, y: 77, size: 8, rotate: -20, depth: 0.35, phone: { x: 18, y: 58 } },
      { name: "heart", x: 95, y: 90, size: 16, rotate: -16, depth: 1, desktopOnly: true },
    ],
  },
];
