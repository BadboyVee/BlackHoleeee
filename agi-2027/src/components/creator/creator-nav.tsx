"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { House, Layers, Megaphone, UserRound, Wallet, type LucideIcon } from "lucide-react";
import { MotionConfig, motion } from "motion/react";

import { LogoMark } from "@/components/brand/logo";
import { isActivePath } from "@/lib/nav";
import { cn } from "@/lib/utils";

import { pressed, springMove, springPop } from "./motion";

type Tab = { href: string; label: string; short: string; icon: LucideIcon };

// Icons are components, so the tabs live here (client side) instead of
// arriving as props from the layout.
const TABS: Tab[] = [
  { href: "/dashboard", label: "Home", short: "Home", icon: House },
  { href: "/dashboard/campaigns", label: "Campaigns", short: "Campaigns", icon: Megaphone },
  { href: "/dashboard/my-campaigns", label: "My campaigns", short: "Mine", icon: Layers },
  { href: "/dashboard/earnings", label: "Earnings", short: "Earnings", icon: Wallet },
  { href: "/dashboard/profile", label: "Profile", short: "Profile", icon: UserRound },
];

/** A campaign's own page: the tab bar steps aside for the claim bar there. */
export function isCampaignPage(pathname: string | null) {
  return pathname ? /^\/dashboard\/campaigns\/[^/]+\/?$/.test(pathname) : false;
}

/** Springs for everything inside; transforms switch off for people who ask for reduced motion. */
export function CreatorMotion({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}

/* ------------------------------------------------------------ phone tabs */

function TabBarItems({ pathname }: { pathname: string | null }) {
  return (
    <>
      {TABS.map((tab) => {
        const active = pathname ? isActivePath(pathname, tab.href) : false;
        const Icon = tab.icon;
        return (
          <motion.div key={tab.href} whileTap={pressed} className="flex min-w-0 flex-1">
            <Link
              href={tab.href}
              aria-current={active ? "page" : undefined}
              aria-label={tab.label}
              className={cn(
                "group flex min-h-14 w-full flex-col items-center justify-center gap-1 rounded-2xl text-[10.5px] leading-none font-medium tracking-[-0.005em] transition-colors",
                active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <span className="relative flex h-8 w-[3.25rem] items-center justify-center">
                {active ? (
                  <motion.span
                    layoutId="creator-tab-pill"
                    transition={springMove}
                    className="absolute inset-0 rounded-full bg-foreground shadow-[0_6px_14px_-6px_rgb(var(--shadow-rgb)/0.5)]"
                  />
                ) : null}
                <motion.span
                  key={active ? "on" : "off"}
                  initial={active ? { scale: 0.7 } : false}
                  animate={{ scale: 1 }}
                  transition={springPop}
                  className="relative flex"
                >
                  <Icon className={cn("size-[21px]", active && "text-background")} strokeWidth={active ? 2.2 : 1.8} />
                </motion.span>
              </span>
              <span className={cn("max-w-full truncate px-0.5", active && "font-semibold")}>{tab.short}</span>
            </Link>
          </motion.div>
        );
      })}
    </>
  );
}

function ActiveTabBar() {
  const pathname = usePathname();
  const hidden = isCampaignPage(pathname);
  return (
    <motion.nav
      aria-label="Main"
      inert={hidden}
      aria-hidden={hidden || undefined}
      initial={false}
      animate={{ y: hidden ? "140%" : "0%" }}
      transition={springMove}
      className="fixed inset-x-0 bottom-0 z-40 px-3 pb-[max(env(safe-area-inset-bottom),0.625rem)] lg:hidden"
    >
      <TabBarShell>
        <TabBarItems pathname={pathname} />
      </TabBarShell>
    </motion.nav>
  );
}

function TabBarShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex max-w-md items-stretch gap-0.5 rounded-[1.75rem] border border-border-strong/70 bg-surface/85 p-1 shadow-float backdrop-blur-xl backdrop-saturate-150">
      {children}
    </div>
  );
}

/** Bottom tab bar for phones and tablets. */
export function CreatorTabBar() {
  return (
    <Suspense
      fallback={
        <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 px-3 pb-[max(env(safe-area-inset-bottom),0.625rem)] lg:hidden">
          <TabBarShell>
            <TabBarItems pathname={null} />
          </TabBarShell>
        </nav>
      }
    >
      <ActiveTabBar />
    </Suspense>
  );
}

/* ---------------------------------------------------------- desktop rail */

function RailItems({ pathname }: { pathname: string | null }) {
  return (
    <>
      {TABS.map((tab) => {
        const active = pathname ? isActivePath(pathname, tab.href) : false;
        const Icon = tab.icon;
        return (
          <motion.div key={tab.href} whileTap={pressed}>
            <Link
              href={tab.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group flex w-full flex-col items-center gap-1.5 rounded-2xl py-1.5 text-[11px] leading-tight font-medium transition-colors",
                active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <span className="relative flex h-10 w-14 items-center justify-center">
                {active ? (
                  <motion.span
                    layoutId="creator-rail-pill"
                    transition={springMove}
                    className="absolute inset-0 rounded-2xl bg-foreground shadow-[0_8px_18px_-8px_rgb(var(--shadow-rgb)/0.55)]"
                  />
                ) : (
                  <span className="absolute inset-0 rounded-2xl bg-surface-2 opacity-0 transition-opacity group-hover:opacity-100" />
                )}
                <Icon className={cn("relative size-5", active && "text-background")} strokeWidth={active ? 2.2 : 1.8} />
              </span>
              <span className={cn("max-w-full px-1 text-center text-balance", active && "font-semibold")}>{tab.label}</span>
            </Link>
          </motion.div>
        );
      })}
    </>
  );
}

function ActiveRailItems() {
  return <RailItems pathname={usePathname()} />;
}

/** Slim left rail for desktop. */
export function CreatorRail() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[5.75rem] flex-col items-center border-r bg-surface/55 py-5 backdrop-blur-xl lg:flex">
      <Link
        href="/dashboard"
        aria-label="Creator home"
        className="pressable mb-7 flex size-11 items-center justify-center rounded-2xl bg-foreground text-background shadow-soft"
      >
        <LogoMark className="size-5" />
      </Link>
      <nav aria-label="Main" className="flex w-full flex-col gap-2 px-2">
        <Suspense fallback={<RailItems pathname={null} />}>
          <ActiveRailItems />
        </Suspense>
      </nav>
    </aside>
  );
}
