import { combinedFollowers, creatorRoster, ROSTER_AS_OF } from "@/lib/creator-roster";
import { showcaseBrands, showcasePosts, statsDates, totalViews } from "@/lib/showcase-posts";

/**
 * Home page copy. Stats, logos, featured posts and the FAQ move into the
 * site_content table with the content editor (Milestone 9) so they can be
 * edited from the admin; until then they live here.
 *
 * The stats and the brand strip are real. The numbers are worked out from the
 * creators in src/lib/creator-roster.ts and the launch posts in
 * src/lib/showcase-posts.ts, so they change when those do. Never type a
 * number in here by hand.
 */

export type Stat = {
  label: string;
  value: number;
  /** compact: 128.6K, rounded down. plain: 14. */
  format: "compact" | "plain";
  suffix?: string;
  /** The days the number comes from ("YYYY-MM-DD"), shown small under the label. One day: from and to match. */
  asOf?: { from: string; to: string } | null;
};

const views = totalViews(showcasePosts);

export const stats: Stat[] = [
  {
    label: "Combined followers on X",
    value: combinedFollowers(creatorRoster),
    format: "compact",
    asOf: ROSTER_AS_OF ? { from: ROSTER_AS_OF, to: ROSTER_AS_OF } : null,
  },
  {
    // Views on the clients' own launch posts, as X showed them. When a post's
    // views couldn't be read (one couldn't), the total is a floor: hence "+".
    label: "Views on our clients' launch posts",
    value: views.views,
    format: "compact",
    suffix: views.partial ? "+" : undefined,
    asOf: statsDates(showcasePosts),
  },
  // The clients in the brand strip and the launch posts. Not "brands launched":
  // micro1's posts were a data commitment and a benchmark, not a brand launch.
  { label: "Brands we've worked with", value: showcaseBrands(showcasePosts).length, format: "plain" },
  // Exactly the creators in the grid, which says others may not be listed yet.
  { label: "Creators on our roster", value: creatorRoster.length, format: "plain" },
];

export type Brand = {
  /** The client's name, written the way they write it. */
  name: string;
  /**
   * The brand's own logo: its X profile picture, from public/posts/. Null
   * when we don't have one, and the name stands alone as a wordmark. Never
   * draw or guess a logo.
   */
  logo: { src: string; shape: "square" | "circle" } | null;
};

/**
 * The marquee under the stats: the owner's real clients, and only those
 * (confirmed 17 Oct 2026). micro1's only picture is Ali Ansari's own photo,
 * not a logo, so micro1 is a wordmark.
 */
export const brands: Brand[] = [
  { name: "Kled AI", logo: { src: "/posts/avatar-kled.webp", shape: "square" } },
  { name: "micro1", logo: null },
  { name: "Maincode", logo: { src: "/posts/avatar-maincode.webp", shape: "square" } },
  { name: "Hedwig", logo: { src: "/posts/avatar-hedwig.webp", shape: "circle" } },
];

export const services = [
  {
    title: "Launch campaigns",
    description:
      "Product drops, funding news and launch days, posted by a coordinated wave of creators inside one window.",
    points: ["One launch window, many voices", "A different angle for every creator", "A shareable report at the end"],
  },
  {
    title: "Always-on posting",
    description: "A steady rhythm of posts every month, so you stay in the conversation between launches.",
    points: ["Monthly posting plan", "Rotating creators and formats"],
  },
  {
    title: "Founder content",
    description: "We help founders post like the best builders on X: threads, demos and build-in-public updates.",
    points: ["Threads and demo posts", "Written with you, posted by you"],
  },
];

export const steps = [
  { title: "Brief", description: "Tell us what you're launching, when, and who it's for." },
  { title: "Match", description: "We pick creators whose audience fits and give each one an angle." },
  { title: "Drop", description: "Creators claim the campaign and get the brief, assets and timing." },
  { title: "Post", description: "They post inside your launch window, labelled as a paid partnership." },
  { title: "Report", description: "You get a private link with every post and the numbers behind it." },
];

export const faqs = [
  {
    question: "How fast can you launch a campaign?",
    answer:
      "Most campaigns go live within a few days of the brief. Tell us your launch date in the booking form and we'll plan backwards from it.",
  },
  {
    question: "How do you pick the creators?",
    answer:
      "Every creator is reviewed before they join. We match on niche, audience and past performance, and we can target specific tiers or hand-pick creators for your launch.",
  },
  {
    question: "Are the posts disclosed as paid?",
    answer:
      "Yes. Every paid post uses X's paid partnership label. Creators confirm it on every submission and we check before approving.",
  },
  {
    question: "What does a campaign cost?",
    answer:
      "Each campaign is scoped to your launch: how many creators, which formats, and over what window. Share a budget range when you book and we'll come back with a plan.",
  },
  {
    question: "What do I get at the end?",
    answer:
      "A private report link with every approved post, plus views, likes, reposts and replies across the campaign. No logins needed, and easy to share with your team or investors.",
  },
  {
    question: "I'm a creator. How do I get paid?",
    answer:
      "Once your proof is approved, the earning shows up in your portal. We pay to your wallet or bank and record every payment with its reference.",
  },
];
