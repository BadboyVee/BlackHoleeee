/*
 * Who may open which part of the site, and where people land after signing
 * in. Plain functions with no Next.js or Supabase imports: the proxy, the
 * sign-in actions and the tests all share them. The database (RLS) is what
 * protects the data; these rules decide which screens people see.
 */

export const ROLES = ["admin", "team", "creator", "applicant"] as const;
export type Role = (typeof ROLES)[number];

/** What the user_role claim can say: a role, or "none" for an account that isn't active. */
export type RoleClaim = Role | "none";

/** Reads the user_role claim the access token hook adds. Undefined when the hook isn't on yet. */
export function parseRoleClaim(value: unknown): RoleClaim | undefined {
  if (value === "none") return "none";
  return typeof value === "string" && (ROLES as readonly string[]).includes(value) ? (value as Role) : undefined;
}

export function isStaff(role: RoleClaim | undefined): boolean {
  return role === "admin" || role === "team";
}

/** Where a signed-in account goes when it can't open a page. */
export const ACCOUNT_UNAVAILABLE_PATH = "/login?status=unavailable";

/** Where each role lands after signing in. */
export function roleHome(role: RoleClaim): string {
  switch (role) {
    case "admin":
    case "team":
      return "/admin";
    case "creator":
      return "/dashboard";
    case "applicant":
      return "/application";
    case "none":
      return ACCOUNT_UNAVAILABLE_PATH;
  }
}

/** Admin pages team members can't open (the ★ pages in PLAN.md). Mirrors adminOnly in admin-nav.ts. */
export const ADMIN_ONLY_PATHS = ["/admin/invites", "/admin/payouts", "/admin/team", "/admin/settings"] as const;

/**
 * The parts of the site with rules:
 * - admin: the agency admin, for staff (admin and team)
 * - creator: the creator portal, for creators, and for staff to see what creators see
 * - applicant: the application status page
 * - staff: the design system page
 * - guest: sign in and sign up, which signed-in people skip
 * - session: setting a new password, which needs the sign-in a reset link gives
 * - open: invite links, for everyone, which read the session when there is one
 */
export type Area = "admin" | "creator" | "applicant" | "staff" | "guest" | "session" | "open";

function under(pathname: string, base: string): boolean {
  return pathname === base || pathname.startsWith(`${base}/`);
}

export function areaFor(pathname: string): Area | null {
  if (under(pathname, "/admin")) return "admin";
  if (under(pathname, "/dashboard")) return "creator";
  if (under(pathname, "/application")) return "applicant";
  if (under(pathname, "/styleguide")) return "staff";
  if (pathname === "/login" || pathname === "/signup") return "guest";
  if (pathname === "/reset-password") return "session";
  if (pathname.startsWith("/invite/")) return "open";
  return null;
}

/** Areas only signed-in people can open. */
export function isPrivateArea(area: Area | null): boolean {
  return area === "admin" || area === "creator" || area === "applicant" || area === "staff";
}

export type Decision = { kind: "allow" } | { kind: "redirect"; to: string };

const allow: Decision = { kind: "allow" };
const redirectTo = (to: string): Decision => ({ kind: "redirect", to });

/**
 * May a signed-in person with this role open `pathname`? If not, where do
 * they go instead. `next` is the ?next= of a sign in or sign up page.
 */
export function accessFor(pathname: string, role: RoleClaim, next?: string | null): Decision {
  const area = areaFor(pathname);
  if (area === null || area === "session" || area === "open") return allow;
  if (area === "guest") {
    // An account that isn't active stays on the sign-in page, which explains why.
    return role === "none" ? allow : redirectTo(destinationFor(role, next));
  }
  if (role === "none") return redirectTo(ACCOUNT_UNAVAILABLE_PATH);
  switch (area) {
    case "admin":
      if (!isStaff(role)) return redirectTo(roleHome(role));
      return role !== "admin" && ADMIN_ONLY_PATHS.some((base) => under(pathname, base)) ? redirectTo("/admin") : allow;
    case "creator":
      return role === "creator" || isStaff(role) ? allow : redirectTo(roleHome(role));
    case "applicant":
      return role === "applicant" ? allow : redirectTo(roleHome(role));
    case "staff":
      return isStaff(role) ? allow : redirectTo(roleHome(role));
  }
}

/** Where a signed-out visitor goes instead of `pathname` (plus its query string), if anywhere. */
export function signedOutRedirect(pathname: string, search = ""): string | null {
  const area = areaFor(pathname);
  if (area === "session") return "/forgot-password?status=expired";
  return isPrivateArea(area) ? loginHref(`${pathname}${search}`) : null;
}

/**
 * Where to go after signing in: the page they were heading for when they
 * can open it, otherwise their role's home.
 */
export function destinationFor(role: RoleClaim, next?: string | null): string {
  const target = safeNextPath(next);
  if (target) {
    const pathname = new URL(target, PLACEHOLDER_ORIGIN).pathname;
    const area = areaFor(pathname);
    if (area !== "guest" && area !== "session" && accessFor(pathname, role).kind === "allow") return target;
  }
  return roleHome(role);
}

/** The sign-in page, remembering where to go afterwards. */
export function loginHref(next?: string | null): string {
  const target = safeNextPath(next);
  return target && target !== "/" ? `/login?next=${encodeURIComponent(target)}` : "/login";
}

const PLACEHOLDER_ORIGIN = "https://agi2027.invalid";

/**
 * A path on this site to go to after signing in, or null. Only same-site
 * paths count: full URLs, protocol-relative "//evil.example", backslashes
 * and control characters are refused, so a link can never send someone to
 * another site. The auth routes themselves are refused too, to avoid loops.
 */
export function safeNextPath(raw: string | null | undefined): string | null {
  if (typeof raw !== "string") return null;
  const value = raw.trim();
  if (!value.startsWith("/") || value.startsWith("//") || /[\\\u0000-\u001f\u007f]/.test(value)) return null;
  let url: URL;
  try {
    url = new URL(value, PLACEHOLDER_ORIGIN);
  } catch {
    return null;
  }
  if (url.origin !== PLACEHOLDER_ORIGIN || under(url.pathname, "/auth")) return null;
  return `${url.pathname}${url.search}`;
}

/**
 * Like safeNextPath, but also accepts a full URL on `origin` (Supabase hands
 * back full URLs in email links), reduced to its path.
 */
export function nextFromUrlOrPath(raw: string | null | undefined, origin: string): string | null {
  if (typeof raw !== "string") return null;
  const value = raw.trim();
  if (/^https?:\/\//i.test(value)) {
    let url: URL;
    try {
      url = new URL(value);
    } catch {
      return null;
    }
    return url.origin === origin ? safeNextPath(`${url.pathname}${url.search}`) : null;
  }
  return safeNextPath(value);
}
