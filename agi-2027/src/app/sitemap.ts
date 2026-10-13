import type { MetadataRoute } from "next";

import { siteConfig } from "@/lib/site";

/*
 * Public pages only. Sign in, the creator portal, the admin and the
 * styleguide stay out (robots.ts also asks crawlers to skip them).
 */
const PUBLIC_PAGES: { path: string; changeFrequency: "daily" | "weekly" | "monthly" | "yearly"; priority: number }[] = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/campaigns", changeFrequency: "daily", priority: 0.9 },
  { path: "/book", changeFrequency: "monthly", priority: 0.9 },
  { path: "/apply", changeFrequency: "monthly", priority: 0.8 },
  { path: "/terms", changeFrequency: "yearly", priority: 0.3 },
  { path: "/privacy", changeFrequency: "yearly", priority: 0.3 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_PAGES.map(({ path, changeFrequency, priority }) => ({
    url: new URL(path, siteConfig.url).toString(),
    changeFrequency,
    priority,
  }));
}
