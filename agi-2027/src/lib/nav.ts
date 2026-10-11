import {
  Banknote,
  Building2,
  ClipboardCheck,
  History,
  House,
  Inbox,
  Layers,
  LayoutDashboard,
  Megaphone,
  PanelsTopLeft,
  Settings,
  ShieldCheck,
  Ticket,
  User,
  UserPlus,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Team members can't open these; only the admin can. */
  adminOnly?: boolean;
};

export type NavGroup = { label: string; items: NavItem[] };

export const marketingNav = [
  { href: "/campaigns", label: "Campaigns" },
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#creators", label: "Creators" },
  { href: "/#faq", label: "FAQ" },
] as const;

export const creatorNav: NavItem[] = [
  { href: "/dashboard", label: "Home", icon: House },
  { href: "/dashboard/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/dashboard/my-campaigns", label: "My campaigns", icon: Layers },
  { href: "/dashboard/earnings", label: "Earnings", icon: Wallet },
  { href: "/dashboard/profile", label: "Profile", icon: User },
];

const overview: NavItem = { href: "/admin", label: "Overview", icon: LayoutDashboard };
const campaigns: NavItem = { href: "/admin/campaigns", label: "Campaigns", icon: Megaphone };
const review: NavItem = { href: "/admin/review", label: "Review queue", icon: ClipboardCheck };
const creators: NavItem = { href: "/admin/creators", label: "Creators", icon: Users };

export const adminNavGroups: NavGroup[] = [
  { label: "Run", items: [overview, campaigns, review] },
  {
    label: "People",
    items: [
      creators,
      { href: "/admin/applications", label: "Applications", icon: Inbox },
      { href: "/admin/invites", label: "Invites", icon: Ticket, adminOnly: true },
      { href: "/admin/team", label: "Team", icon: ShieldCheck, adminOnly: true },
    ],
  },
  {
    label: "Money",
    items: [{ href: "/admin/payouts", label: "Payouts", icon: Banknote, adminOnly: true }],
  },
  {
    label: "Growth",
    items: [
      { href: "/admin/clients", label: "Clients", icon: Building2 },
      { href: "/admin/leads", label: "Leads", icon: UserPlus },
      { href: "/admin/content", label: "Site content", icon: PanelsTopLeft },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/admin/settings", label: "Settings", icon: Settings, adminOnly: true },
      { href: "/admin/activity", label: "Activity log", icon: History },
    ],
  },
];

/** The four admin screens that get a tab on phones; the rest sit under More. */
export const adminTabs: NavItem[] = [overview, review, campaigns, creators];

/** Root paths only match exactly; everything else matches its sub-pages too. */
export function isActivePath(pathname: string, href: string) {
  if (href === "/dashboard" || href === "/admin") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}
