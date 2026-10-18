/**
 * Real launch posts on X, sent by the owner on 12 Oct 2026. The text is copied
 * word for word from the owner's screenshots, the numbers are exactly what X
 * showed that day, and the pictures are cropped from the same screenshots.
 * Each one links to the live post. A number that couldn't be read is left out,
 * never guessed. `postedAt` is decoded from the post's ID (X post IDs carry
 * their creation time), and a unit test keeps the two in step.
 */

export type ShowcasePost = {
  /** The X post ID. */
  id: string;
  url: string;
  /**
   * The client whose launch this was, as they write their name. Not always
   * the author: Ali Ansari posts for micro1. The home page counts the brands
   * from this, so two posts for one client count once.
   */
  brand: string;
  author: {
    name: string;
    handle: string;
    avatar: string;
    /** Business accounts on X have square avatars, people round ones. */
    avatarShape: "square" | "circle";
    badge: "gold" | "blue";
  };
  /** Paragraphs are separated by a blank line, as on X. */
  text: string;
  /** Bare links in the text, shown in blue like X does. */
  links?: string[];
  postedAt: string;
  media: {
    kind: "video" | "image" | "link";
    src: string;
    width: number;
    height: number;
    alt: string;
    /** Which part to keep when the picture is cropped to fit (CSS object-position). */
    focus?: string;
    /** The site a link preview comes from. */
    from?: string;
  };
  /** As X shows them ("3.7M", "3K"), on the day in STATS_AS_OF. */
  stats: { views?: string; replies?: string; reposts?: string; likes?: string; bookmarks?: string };
};

/** The day the owner's screenshots were taken, which the numbers come from. */
export const STATS_AS_OF = "2026-10-12";

export const showcasePosts: ShowcasePost[] = [
  {
    id: "2105311618284527767",
    url: "https://x.com/useKled/status/2105311618284527767",
    brand: "Kled AI",
    author: { name: "Kled AI", handle: "useKled", avatar: "/posts/avatar-kled.webp", avatarShape: "square", badge: "gold" },
    text: "This is Kled V3. We’ve solved data collection for artificial general intelligence.\n\nAny consumer dataset that can exist, can now be collected from physical reality in under 72 hours.\n\nAll powered by the largest and most comprehensive data application layer on the planet. (Thread)",
    postedAt: "2026-09-30T14:59:39Z",
    media: {
      kind: "video",
      src: "/posts/media-kled.webp",
      width: 800,
      height: 552,
      alt: "Still from Kled’s V3 video: a person walks into a lamp-lit living room set, captioned “Kled 3.0, Human demonstration collection”.",
    },
    stats: { views: "3.7M", replies: "178", reposts: "167", likes: "3K", bookmarks: "387" },
  },
  {
    id: "2108613100413096046",
    url: "https://x.com/aliansarinik/status/2108613100413096046",
    brand: "micro1",
    author: { name: "Ali Ansari", handle: "aliansarinik", avatar: "/posts/avatar-ali.webp", avatarShape: "circle", badge: "blue" },
    text: "Today micro1 is announcing a commitment to spend $1B over the next 12 months on the acquisition & licensing of enterprise data for AI training, with financial backing from Citi and Hercules.",
    postedAt: "2026-10-09T17:38:33Z",
    media: {
      kind: "link",
      src: "/posts/media-micro1.webp",
      width: 800,
      height: 416,
      alt: "Link preview from micro1.ai: “micro1. Committing to acquire $1B of enterprise data”.",
      from: "micro1.ai",
    },
    stats: { views: "171K", replies: "86", reposts: "118", likes: "769" },
  },
  {
    id: "2105230308132225289",
    url: "https://x.com/MaincodeAU/status/2105230308132225289",
    brand: "Maincode",
    author: { name: "Maincode", handle: "MaincodeAU", avatar: "/posts/avatar-maincode.webp", avatarShape: "square", badge: "gold" },
    text: "Today we are open-sourcing Matilda Jev, Australia’s first decision model, conditioned for Australian deployment and post-trained with our own specialised recipe. Decision models do not generate text. They answer a typed question and respond with a calibrated probability for each option in a single forward pass, reducing hallucination and making intelligent decisions faster and more efficient.\n\nThis release proves that highly capable AI models can be built, post-trained, evaluated, and served entirely within Australia. Post-trained end-to-end on our local infrastructure, the model achieved a median decision latency of 56.8ms on a single @AMD MI355X across 150,317 evaluation requests.",
    postedAt: "2026-09-30T09:36:33Z",
    media: {
      kind: "image",
      src: "/posts/media-maincode.webp",
      width: 800,
      height: 801,
      alt: "Chart: Matilda Jev tops the Jev Decision Index with 59.26, ahead of seven other models.",
      focus: "50% 0%",
    },
    stats: { views: "1.8M", replies: "315", reposts: "258", likes: "2.7K", bookmarks: "121" },
  },
  {
    id: "2107497652871155953",
    url: "https://x.com/aliansarinik/status/2107497652871155953",
    brand: "micro1",
    author: { name: "Ali Ansari", handle: "aliansarinik", avatar: "/posts/avatar-ali.webp", avatarShape: "circle", badge: "blue" },
    text: "Which personal agent is the best life assistant?\n\nToday we’re releasing the micro1 PersonalAgentBench to help answer that, and we’re paying real personal agent users to contribute to the benchmark.\n\nPersonal agents can now book your flights, answer emails, and move your meetings around. That’s great, until one messages the wrong person or makes a purchase without confirming.\n\nCapability is not the same as trust. So we put four personal agents to the test: Instinct, Muse, Grok Bot, and Gemini Spark. We found that even when agents found the right information, they still often miss what matters, overshare, or make things up.\n\nTo find out for yourself how your agent compares, you can join our benchmark. We’re paying the first 100 users to run our prompts and share their results.",
    postedAt: "2026-10-06T15:46:10Z",
    media: {
      kind: "image",
      src: "/posts/media-ali.webp",
      width: 800,
      height: 316,
      alt: "micro1 PersonalAgentBench artwork: dozens of small black and blue characters scattered on white.",
    },
    // The counts on this one were cut off in the screenshot, so none are shown.
    stats: {},
  },
  {
    id: "2106449214536605976",
    url: "https://x.com/hedwigdotco/status/2106449214536605976",
    brand: "Hedwig",
    author: { name: "Hedwig", handle: "hedwigdotco", avatar: "/posts/avatar-hedwig.webp", avatarShape: "circle", badge: "blue" },
    text: "we’re going to kill a one trillion dollar industry.\n\nwe’re building Hedwig: one visual workspace that connects your tools and gives your agent the full picture, and going after the biggest players like google and meta.\n\nbuilt by a team from stanford, meta, and polymarket.\n\nloved by 6,000+ across the world\n\ncomment + RT for free access\n\nhedwigmail.com",
    links: ["hedwigmail.com"],
    postedAt: "2026-10-03T18:20:03Z",
    media: {
      kind: "video",
      src: "/posts/media-hedwig.webp",
      width: 800,
      height: 445,
      alt: "Still from Hedwig’s video: Gmail, Sheets, Docs, Calendar, Meet and Notion icons circling the words “lived in one place”.",
    },
    stats: { views: "456K", replies: "318", reposts: "321", likes: "1.3K", bookmarks: "999" },
  },
];

export function getShowcasePost(id: string): ShowcasePost {
  const post = showcasePosts.find((item) => item.id === id);
  if (!post) throw new Error(`No showcase post with id ${id}`);
  return post;
}

/** When an X post was created, from its ID: the top bits are milliseconds since X's epoch. */
export function postIdTime(id: string): Date {
  return new Date(Number((BigInt(id) >> BigInt(22)) + BigInt(1288834974657)));
}

export type PostTextPart = { kind: "text" | "mention" | "hashtag" | "link"; text: string };

/** Splits post text so mentions, hashtags and the given bare links can be shown in blue. */
export function splitPostText(text: string, links: string[] = []): PostTextPart[] {
  const escaped = links.map((link) => link.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  // No lookbehind: this also runs in browsers (older Safari can't parse it).
  const pattern = new RegExp([String.raw`@\w{1,15}`, String.raw`#\w+`, ...escaped].join("|"), "g");
  const parts: PostTextPart[] = [];
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0;
    const value = match[0];
    const kind = value.startsWith("@") ? "mention" : value.startsWith("#") ? "hashtag" : "link";
    // "name@site" or "a#b" aren't mentions or hashtags.
    if (kind !== "link" && start > 0 && /[\w@#]/.test(text[start - 1])) continue;
    if (start > last) parts.push({ kind: "text", text: text.slice(last, start) });
    parts.push({ kind, text: value });
    last = start + value.length;
  }
  if (last < text.length) parts.push({ kind: "text", text: text.slice(last) });
  return parts;
}

/**
 * The start of a long post, cut at a word boundary, for places with little
 * room. Returns the text unchanged when it already fits.
 */
export function excerptPost(text: string, max: number): { text: string; cut: boolean } {
  if (text.length <= max) return { text, cut: false };
  const slice = text.slice(0, max);
  const lastSpace = slice.search(/\s\S*$/);
  const cut = (lastSpace > max * 0.6 ? slice.slice(0, lastSpace) : slice).replace(/[\s,.;:]+$/, "");
  return { text: `${cut}…`, cut: true };
}

/**
 * A count the way X shows it back to a whole number: "3.7M" is 3,700,000,
 * "171K" is 171,000, "6,237" is 6,237. Exact (no floating point drift), and
 * null for anything that isn't a count.
 */
export function parseXCount(value: string | undefined): number | null {
  const match = /^(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?([KMB])?$/.exec(value?.trim() ?? "");
  if (!match) return null;
  const [, whole, fraction = "", unit] = match;
  const scale = unit === "B" ? 1_000_000_000 : unit === "M" ? 1_000_000 : unit === "K" ? 1_000 : 1;
  // "3.7" without a K or M isn't a count.
  if (fraction && scale === 1) return null;
  const digits = Number(whole.replace(/,/g, ""));
  return digits * scale + Math.round((Number(fraction || "0") * scale) / 10 ** fraction.length);
}

/** X's short counts back to numbers, for ordering: -1 when there's none. */
export function statNumber(value: string | undefined): number {
  return parseXCount(value) ?? -1;
}

/**
 * The views X showed on these posts, added up. `partial` is true when a post's
 * views couldn't be read, so the real total is at least `views`.
 */
export function totalViews(posts: ShowcasePost[]): { views: number; partial: boolean } {
  let views = 0;
  let partial = false;
  for (const post of posts) {
    const count = parseXCount(post.stats.views);
    if (count === null) partial = true;
    else views += count;
  }
  return { views, partial };
}

/** The brands these posts launched for, each once, in the order they first appear. */
export function showcaseBrands(posts: ShowcasePost[]): string[] {
  return [...new Set(posts.map((post) => post.brand))];
}

/** Most viewed first; posts whose views we don't know go last, in their given order. */
export function byViews(posts: ShowcasePost[]): ShowcasePost[] {
  return [...posts].sort((a, b) => statNumber(b.stats.views) - statNumber(a.stats.views));
}

/**
 * The frame a post's picture gets: its own shape when it's 16:10 or wider (so
 * link previews and banners keep their edges), cropped to 16:10 when taller.
 */
export function mediaAspect(media: ShowcasePost["media"]): string {
  return media.width / media.height >= 1.6 ? `${media.width} / ${media.height}` : "16 / 10";
}
