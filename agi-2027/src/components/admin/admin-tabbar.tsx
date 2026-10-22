"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { Ellipsis, Plus } from "lucide-react";

import { LookPicker } from "@/components/theme/look-picker";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { showSampleData } from "@/lib/sample-data";

import { adminTabs, isActiveAdminPath, isBuilderPath } from "./admin-nav";
import { NavGroups, PreviewNote } from "./admin-sidebar";
import { springArrive, springMove } from "./motion";

const tabClass =
  "relative flex min-h-14 flex-1 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl px-1 text-[11px] font-medium transition-colors";

function ActiveMark() {
  return (
    <motion.span
      layoutId="admin-tab-active"
      transition={springMove}
      aria-hidden
      className="absolute inset-x-4 top-0 h-0.5 rounded-full bg-foreground"
    />
  );
}

function MoreSheet({ pathname, active }: { pathname: string | null; active: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger className={cn(tabClass, active ? "text-foreground" : "text-subtle-foreground hover:text-foreground")}>
        {active ? <ActiveMark /> : null}
        <Ellipsis className="size-[21px]" strokeWidth={active ? 2.1 : 1.7} aria-hidden />
        <span>More</span>
      </SheetTrigger>
      <SheetContent side="bottom" className="gap-0">
        <SheetHeader className="px-5 pt-5 pb-3">
          <SheetTitle>Every section</SheetTitle>
          <SheetDescription>Everything in the agency admin, plus the look of the site.</SheetDescription>
        </SheetHeader>
        <nav aria-label="All admin sections" className="min-h-0 overflow-y-auto px-3 pb-4">
          <NavGroups pathname={pathname} layoutKey="sheet" onNavigate={() => setOpen(false)} />
        </nav>
        <div className="flex flex-col gap-3 border-t px-5 pt-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">Appearance</p>
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <LookPicker />
            </div>
          </div>
          <PreviewNote className="-mx-2" />
        </div>
      </SheetContent>
    </Sheet>
  );
}

function TabBar({ pathname }: { pathname: string | null }) {
  const hidden = pathname ? isBuilderPath(pathname) : false;
  const onCampaignPage = pathname ? /^\/admin\/campaigns\/(?!new$)[^/]+$/.test(pathname) : false;
  const moreActive = pathname ? !adminTabs.some((tab) => isActiveAdminPath(pathname, tab.href)) : false;

  return (
    <>
      <AnimatePresence>
        {/* New campaign only saves on preview links for now, so the live site doesn't offer it. */}
        {showSampleData() && !hidden && !onCampaignPage ? (
          <motion.div
            key="fab"
            initial={{ opacity: 0, scale: 0.85, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 8 }}
            transition={springArrive}
            className="fixed right-4 bottom-[calc(4.5rem+max(env(safe-area-inset-bottom),0.5rem))] z-40 lg:hidden"
          >
            <Link
              href="/admin/campaigns/new"
              className="pressable inline-flex h-12 items-center gap-2 rounded-full bg-primary pr-5 pl-4 text-[15px] font-medium text-primary-foreground shadow-float"
            >
              <Plus className="size-5" aria-hidden />
              New campaign
            </Link>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {hidden ? null : (
        <nav
          aria-label="Admin"
          className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/90 pt-1 pb-safe backdrop-blur-xl lg:hidden"
        >
          <div className="mx-auto flex max-w-lg items-stretch px-1">
            {adminTabs.map((tab) => {
              const active = pathname ? isActiveAdminPath(pathname, tab.href) : false;
              const Icon = tab.icon;
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(tabClass, active ? "text-foreground" : "text-subtle-foreground hover:text-foreground")}
                >
                  {active ? <ActiveMark /> : null}
                  <span className="relative">
                    <Icon className="size-[21px]" strokeWidth={active ? 2.1 : 1.7} aria-hidden />
                    {tab.count ? (
                      <span className="absolute -top-1.5 -right-3 min-w-[18px] rounded-full bg-foreground px-1 text-center font-mono text-[10px] leading-[18px] font-medium text-background ring-2 ring-background">
                        {tab.count}
                        <span className="sr-only"> waiting</span>
                      </span>
                    ) : null}
                  </span>
                  <span className="max-w-full truncate">{tab.label}</span>
                </Link>
              );
            })}
            <MoreSheet pathname={pathname} active={moreActive} />
          </div>
        </nav>
      )}
    </>
  );
}

function ActiveTabBar() {
  const pathname = usePathname();
  return <TabBar pathname={pathname} />;
}

/** Phones: four tabs plus More, and on preview links a floating New campaign button. */
export function AdminTabBar() {
  return (
    <Suspense fallback={<TabBar pathname={null} />}>
      <ActiveTabBar />
    </Suspense>
  );
}
