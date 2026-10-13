import { NextResponse, type NextRequest } from "next/server";

import { isLiveSite } from "@/lib/deploy";

/** Areas that run on demo data and have no sign-in yet. */
export const PREVIEW_ONLY_PATHS = ["/admin", "/dashboard", "/styleguide"] as const;

export function isPreviewOnlyPath(pathname: string): boolean {
  return PREVIEW_ONLY_PATHS.some((base) => pathname === base || pathname.startsWith(`${base}/`));
}

/**
 * Until sign-in exists (Milestone 3), the owner's admin and the creator portal
 * run on demo data and anyone could open them. On the live site they send
 * visitors home; preview links and local development still show them so the
 * owner can try everything. Milestone 3 replaces this with real sign-in
 * checks.
 */
export function proxy(request: NextRequest) {
  if (!isLiveSite() || !isPreviewOnlyPath(request.nextUrl.pathname)) {
    return NextResponse.next();
  }
  const home = request.nextUrl.clone();
  home.pathname = "/";
  home.search = "";
  return NextResponse.redirect(home, 307);
}

export const config = {
  matcher: ["/admin/:path*", "/dashboard/:path*", "/styleguide/:path*"],
};
