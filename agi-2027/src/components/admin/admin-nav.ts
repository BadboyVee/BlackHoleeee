import {
  Banknote,
  Building2,
  ClipboardCheck,
  History,
  Inbox,
  LayoutDashboard,
  Megaphone,
  PanelsTopLeft,
  Settings,
  ShieldCheck,
  Ticket,
  UserPlus,
  Users,
  type LucideIcon,
} from "lucide-react";

import { campaignById } from "@/lib/campaigns/demo";
import { showSampleData } from "@/lib/sample-data";
import { demoApplications, demoLeads, reviewCount } from "./demo-insights";

/*
 * The owner's navigation. Only client components import this module, so the
 * icon components never cross from the server to the client.
 *
 * Counts beside the items come from the sample data, so they show on preview
 * links only. The live site shows no counts until the real queues exist.
 */

export type AdminNavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Team members can't open these; only the admin (the owner) can. */
  adminOnly?: boolean;
  /** A count shown beside the item. */
  count?: number;
  /** The count needs action (shown solid) rather than being informational. */
  urgent?: boolean;
  keywords?: string;
};

export type AdminNavGroup = { label: string; items: AdminNavItem[] };

const overview: AdminNavItem = { href: "/admin", label: "Overview", icon: LayoutDashboard, keywords: "home dashboard stats" };
const review: AdminNavItem = {
  href: "/admin/review",
  label: "Review queue",
  icon: ClipboardCheck,
  urgent: true,
  keywords: "approve drafts proof requests",
};
const campaigns: AdminNavItem = { href: "/admin/campaigns", label: "Campaigns", icon: Megaphone, keywords: "list drop" };
const creators: AdminNavItem = { href: "/admin/creators", label: "Creators", icon: Users, keywords: "directory people roster" };

const navGroups: AdminNavGroup[] = [
  {
    label: "Run",
    items: [
      overview,
      review,
      campaigns,
      creators,
      { href: "/admin/applications", label: "Applications", icon: Inbox, keywords: "apply approve new creators" },
      { href: "/admin/invites", label: "Invites", icon: Ticket, adminOnly: true, keywords: "invite links" },
    ],
  },
  {
    label: "Business",
    items: [
      { href: "/admin/payouts", label: "Payouts", icon: Banknote, adminOnly: true, keywords: "pay money earnings unpaid" },
      { href: "/admin/clients", label: "Clients", icon: Building2, keywords: "brands startups" },
      { href: "/admin/leads", label: "Leads", icon: UserPlus, keywords: "book a campaign inquiries" },
      { href: "/admin/content", label: "Site content", icon: PanelsTopLeft, keywords: "homepage stats logos faq" },
    ],
  },
  {
    label: "Agency",
    items: [
      { href: "/admin/team", label: "Team", icon: ShieldCheck, adminOnly: true, keywords: "staff roles invite" },
      { href: "/admin/settings", label: "Settings", icon: Settings, adminOnly: true, keywords: "telegram currencies email" },
      { href: "/admin/activity", label: "Activity", icon: History, keywords: "log audit history" },
    ],
  },
];

/** The four screens that get a tab on phones; everything else sits under More. */
const navTabs: AdminNavItem[] = [overview, { ...review, label: "Review" }, campaigns, creators];

/** Sample counts by href, on preview links only. The live site gets none. */
export function sampleNavCounts(showSamples: boolean): Record<string, number> {
  if (!showSamples) return {};
  return {
    "/admin/review": reviewCount(),
    "/admin/applications": demoApplications.length,
    "/admin/leads": demoLeads.length,
  };
}

function withCounts(items: AdminNavItem[], counts: Record<string, number>): AdminNavItem[] {
  return items.map((item) => (counts[item.href] ? { ...item, count: counts[item.href] } : item));
}

/** Every section, grouped. Pass showSampleData(); false leaves out every sample count. */
export function adminNavGroupsFor(showSamples: boolean): AdminNavGroup[] {
  const counts = sampleNavCounts(showSamples);
  return navGroups.map((group) => ({ ...group, items: withCounts(group.items, counts) }));
}

/** The phone tabs. Pass showSampleData(); false leaves out every sample count. */
export function adminTabsFor(showSamples: boolean): AdminNavItem[] {
  return withCounts(navTabs, sampleNavCounts(showSamples));
}

const SHOW_SAMPLES = showSampleData();

export const adminNavGroups = adminNavGroupsFor(SHOW_SAMPLES);

export const adminTabs = adminTabsFor(SHOW_SAMPLES);

export const allAdminNavItems = adminNavGroups.flatMap((group) => group.items);

/** Overview only matches exactly; every other section matches its sub-pages too. */
export function isActiveAdminPath(pathname: string, href: string) {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** The builder gets the whole phone screen: no tab bar, no floating button. */
export function isBuilderPath(pathname: string) {
  return pathname === "/admin/campaigns/new" || /^\/admin\/campaigns\/[^/]+\/edit$/.test(pathname);
}

export type Crumb = { label: string; href?: string };

const extraLabels: Record<string, string> = { "/admin/notifications": "Notifications" };

/**
 * Breadcrumbs for a path, e.g. Campaigns / Nebula 2.0 launch day / Edit. A
 * campaign's title comes from the sample data on preview links only; the live
 * site says "Campaign" until real campaigns exist.
 */
export function crumbsFor(pathname: string, showSamples: boolean = SHOW_SAMPLES): Crumb[] {
  if (pathname === "/admin") return [{ label: "Overview" }];
  const campaignMatch = /^\/admin\/campaigns\/([^/]+)(\/edit)?$/.exec(pathname);
  if (campaignMatch) {
    const [, id, edit] = campaignMatch;
    if (id === "new") return [{ label: "Campaigns", href: "/admin/campaigns" }, { label: "New campaign" }];
    const title = (showSamples ? campaignById(id)?.title : undefined) ?? "Campaign";
    return edit
      ? [{ label: "Campaigns", href: "/admin/campaigns" }, { label: title, href: `/admin/campaigns/${id}` }, { label: "Edit" }]
      : [{ label: "Campaigns", href: "/admin/campaigns" }, { label: title }];
  }
  const item = allAdminNavItems.find((entry) => entry.href !== "/admin" && isActiveAdminPath(pathname, entry.href));
  if (item) return [{ label: item.label }];
  return [{ label: extraLabels[pathname] ?? "Admin" }];
}
