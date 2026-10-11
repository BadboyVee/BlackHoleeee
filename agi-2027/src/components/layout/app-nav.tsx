"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Ellipsis } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import {
  adminNavGroups,
  adminTabs,
  creatorNav,
  isActivePath,
  type NavGroup,
  type NavItem,
} from "@/lib/nav";
import { cn } from "@/lib/utils";

export type Area = "creator" | "admin";

// Icons are components, which can't be passed from Server Components, so the
// navigation reads its config here instead of taking it as props.
const sideNavGroups: Record<Area, NavGroup[]> = {
  creator: [{ label: "", items: creatorNav }],
  admin: adminNavGroups,
};
const tabItems: Record<Area, NavItem[]> = { creator: creatorNav, admin: adminTabs };

/*
 * Active-link highlighting reads the URL, which isn't known while a page with
 * an unknown dynamic segment prerenders. Each list renders once without a
 * highlight as the Suspense fallback, so the shell stays in the static HTML.
 */

function SideNavList({
  groups,
  pathname,
  onNavigate,
}: {
  groups: NavGroup[];
  pathname: string | null;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex flex-col gap-5">
      {groups.map((group) => (
        <div key={group.label || "main"} className="flex flex-col gap-0.5">
          {group.label ? (
            <p className="px-3 pb-1.5 text-label text-subtle-foreground">{group.label}</p>
          ) : null}
          {group.items.map((item) => {
            const active = pathname ? isActivePath(pathname, item.href) : false;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "group relative flex min-h-11 items-center gap-3 rounded-xl border px-3 text-sm font-medium transition-[color,background-color,box-shadow] lg:min-h-9",
                  active
                    ? "border-border bg-surface text-foreground shadow-soft"
                    : "border-transparent text-muted-foreground hover:bg-surface/60 hover:text-foreground",
                )}
              >
                <item.icon
                  className={cn(
                    "size-[17px] shrink-0 transition-colors",
                    active ? "text-foreground" : "text-subtle-foreground group-hover:text-foreground",
                  )}
                />
                <span className="truncate">{item.label}</span>
                {item.adminOnly ? (
                  <span className="ml-auto text-[10px] font-medium tracking-wide text-subtle-foreground uppercase">
                    Admin
                  </span>
                ) : null}
              </Link>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function ActiveSideNavList(props: { groups: NavGroup[]; onNavigate?: () => void }) {
  const pathname = usePathname();
  return <SideNavList {...props} pathname={pathname} />;
}

function SideNav({ area, onNavigate }: { area: Area; onNavigate?: () => void }) {
  const groups = sideNavGroups[area];
  return (
    <Suspense fallback={<SideNavList groups={groups} pathname={null} />}>
      <ActiveSideNavList groups={groups} onNavigate={onNavigate} />
    </Suspense>
  );
}

const tabClass =
  "relative flex min-h-14 flex-1 flex-col items-center justify-center gap-1 rounded-xl px-1 text-[11px] font-medium transition-colors";

function TabBarList({
  items,
  pathname,
  more,
}: {
  items: NavItem[];
  pathname: string | null;
  more?: React.ReactNode;
}) {
  return (
    <>
      {items.map((item) => {
        const active = pathname ? isActivePath(pathname, item.href) : false;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(tabClass, active ? "text-foreground" : "text-subtle-foreground hover:text-foreground")}
          >
            <item.icon className="size-[22px]" strokeWidth={active ? 2.1 : 1.7} />
            <span className="max-w-full truncate">{item.label.replace("My campaigns", "Mine")}</span>
            {active ? <span aria-hidden className="absolute bottom-1 size-1 rounded-full bg-(--tone-brand)" /> : null}
          </Link>
        );
      })}
      {more}
    </>
  );
}

function ActiveTabBarList(props: { items: NavItem[]; more?: React.ReactNode }) {
  const pathname = usePathname();
  return <TabBarList {...props} pathname={pathname} />;
}

/** Bottom tab bar for phones. Admin gets a "More" tab that opens every section. */
function BottomTabBar({ area }: { area: Area }) {
  const items = tabItems[area];
  const more = area === "admin" ? <MoreTab /> : undefined;
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/85 px-2 pt-1 pb-safe backdrop-blur-xl lg:hidden"
    >
      <div className="mx-auto flex max-w-md items-stretch">
        <Suspense fallback={<TabBarList items={items} pathname={null} more={more} />}>
          <ActiveTabBarList items={items} more={more} />
        </Suspense>
      </div>
    </nav>
  );
}

function MoreTab() {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger className={cn(tabClass, "cursor-pointer text-subtle-foreground hover:text-foreground")}>
        <Ellipsis className="size-[22px]" strokeWidth={1.8} />
        <span>More</span>
      </SheetTrigger>
      <SheetContent side="bottom" className="gap-0">
        <SheetHeader className="pb-2">
          <SheetTitle>
            <Logo />
          </SheetTitle>
          <SheetDescription className="sr-only">Every admin section</SheetDescription>
        </SheetHeader>
        <div className="overflow-y-auto px-5 pb-6">
          <SideNav area="admin" onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}

export { BottomTabBar, SideNav };
