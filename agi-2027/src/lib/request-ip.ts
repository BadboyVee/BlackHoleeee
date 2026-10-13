/**
 * The visitor's IP address, read from the header the host sets itself.
 * Vercel overwrites x-forwarded-for with the real address; Netlify puts it in
 * x-nf-client-connection-ip. Any other header may have come from the visitor,
 * who could then pick a new address for every request and slip past the
 * rate limit. `host` is the AGI_DEPLOY_HOST baked in at build.
 */
export function clientIp(list: Headers, host: string | undefined = process.env.AGI_DEPLOY_HOST): string {
  if (host === "netlify") return list.get("x-nf-client-connection-ip")?.trim() || "unknown";
  // Vercel, and local development, where nothing is at stake.
  const forwarded = list.get("x-forwarded-for")?.split(",")[0]?.trim();
  if (forwarded) return forwarded;
  return list.get("x-real-ip")?.trim() || "unknown";
}
