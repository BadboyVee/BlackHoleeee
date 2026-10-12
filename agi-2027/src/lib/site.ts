function resolveSiteUrl() {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL;
  const vercelHost =
    process.env.VERCEL_ENV === "production"
      ? process.env.VERCEL_PROJECT_PRODUCTION_URL
      : process.env.VERCEL_URL;
  if (vercelHost) return `https://${vercelHost}`;
  return "http://localhost:3000";
}

export const siteConfig = {
  name: "AGI 2027",
  tagline: "Creator marketing for AI launches",
  description:
    "AGI 2027 gets AI and tech launches seen. We brief the creators your users already follow, they post on X, and you get a clear report on what it did.",
  url: resolveSiteUrl(),
  /**
   * Where visitors reach the agency: the "email us" links only. The owner
   * asked (12 Oct 2026) that nothing automated is sent here; booking
   * alerts go to LEADS_NOTIFY_EMAIL. NEXT_PUBLIC_CONTACT_EMAIL overrides it.
   */
  contactEmail: process.env.NEXT_PUBLIC_CONTACT_EMAIL || "joshhthepluggg@gmail.com",
  /** The agency's X profile. Empty until it is set. */
  xUrl: process.env.NEXT_PUBLIC_X_URL ?? "",
} as const;
