import type { NextConfig } from "next";

import { deployHostFrom, deployStageFrom, deployUrlFrom } from "./src/lib/deploy";

// HSTS is added at launch, once the custom domain is settled.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), browsing-topics=()" },
];

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  poweredByHeader: false,
  // Worked out while building, on Vercel or Netlify (see src/lib/deploy.ts).
  env: {
    AGI_DEPLOY_STAGE: deployStageFrom(process.env),
    AGI_DEPLOY_URL: deployUrlFrom(process.env),
    AGI_DEPLOY_HOST: deployHostFrom(process.env),
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
