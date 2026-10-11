/**
 * Home page copy and placeholder content. Stats, logos, featured posts and the
 * FAQ move into the site_content table in Milestone 2 so they can be edited
 * from the admin; until then they live here. Brands, creators and numbers
 * below are placeholders, not real companies or people.
 */

export const hero = {
  eyebrow: "Creator marketing for AI launches",
  title: ["Your launch,", "on every"],
  titleAccent: "timeline",
  lead: "AGI 2027 puts AI and tech launches in front of millions through the creators their users already follow. Briefed in hours, posted on time, measured in one report you can share.",
};

export type Stat = { label: string; value: number; format: "compact" | "plain"; suffix?: string };

export const stats: Stat[] = [
  { label: "Combined followers", value: 12_400_000, format: "compact" },
  { label: "Views every month", value: 85_000_000, format: "compact" },
  { label: "Campaigns run", value: 140, format: "plain", suffix: "+" },
  { label: "Creators in the network", value: 15, format: "plain" },
];

export const brands = [
  "Nebula",
  "Vectorline",
  "Orbitar",
  "Lumen Labs",
  "Parallax",
  "Quanta",
  "Helix",
  "Northwind",
];

export type FeaturedPost = {
  creator: { name: string; handle: string; initials: string; hue: number };
  brand: string;
  moment: string;
  text: string;
  metrics: { views: number; likes: number; reposts: number };
};

export const featuredPosts: FeaturedPost[] = [
  {
    creator: { name: "Mira Okafor", handle: "mira_builds", initials: "MO", hue: 95 },
    brand: "Nebula",
    moment: "Launch day",
    text: "Nebula 2.0 shipped agents that actually finish the job. I handed it my content calendar and it planned, drafted and scheduled a full week in four minutes.",
    metrics: { views: 1_240_000, likes: 18_400, reposts: 2_100 },
  },
  {
    creator: { name: "Devon Hale", handle: "devonships", initials: "DH", hue: 210 },
    brand: "Vectorline",
    moment: "Funding news",
    text: "Vectorline just raised to make vector search boring, and boring is the point. Moved a 40M-row index over in an afternoon. p95 went from 180ms to 22ms.",
    metrics: { views: 862_000, likes: 9_800, reposts: 1_400 },
  },
  {
    creator: { name: "Kai Moreno", handle: "kai_codes", initials: "KM", hue: 280 },
    brand: "Orbitar",
    moment: "Product drop",
    text: "Orbitar's design agent turned a napkin sketch into a clickable prototype while my coffee brewed. If you're a founder still hiring for v0, watch this first.",
    metrics: { views: 640_000, likes: 7_200, reposts: 950 },
  },
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

export const creatorPerks = [
  "Pick the campaigns you want. New drops land in your portal and on Telegram.",
  "Clear briefs, your own angle, and assets ready to download.",
  "Paid per post, with every payment and its reference in your portal.",
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
