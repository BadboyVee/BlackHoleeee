import type { MetadataRoute } from "next";

import { siteConfig } from "@/lib/site";

/** Crawl the public site; skip the portal, the admin, the styleguide and the API. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin", "/dashboard", "/styleguide", "/api"],
    },
    sitemap: new URL("/sitemap.xml", siteConfig.url).toString(),
  };
}
