"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, ChevronLeft, Search } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { UserMenu } from "@/components/layout/user-menu";
import { LookPicker } from "@/components/theme/look-picker";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { crumbsFor } from "./admin-nav";
import { useCommandPalette } from "./command-palette";
import { Kbd, useIsApple } from "./kbd";

function Crumbs({ pathname }: { pathname: string | null }) {
  if (!pathname) {
    return <p className="text-label text-subtle-foreground">Agency admin</p>;
  }
  const crumbs = crumbsFor(pathname);
  const current = crumbs[crumbs.length - 1];
  const parent = crumbs.length > 1 ? crumbs[crumbs.length - 2] : undefined;
  return (
    <>
      {/* Phones: a back link and the page name. */}
      <div className="flex min-w-0 items-center gap-1 lg:hidden">
        {parent?.href ? (
          <Button asChild variant="ghost" size="icon-sm" className="-ml-2 shrink-0 text-muted-foreground">
            <Link href={parent.href} aria-label={`Back to ${parent.label}`}>
              <ChevronLeft className="size-5" />
            </Link>
          </Button>
        ) : (
          <Link href="/admin" aria-label="Agency admin home" className="mr-1.5 shrink-0 rounded-md">
            <LogoMark className="size-5" />
          </Link>
        )}
        <p className="min-w-0 truncate text-[15px] font-semibold tracking-[-0.01em]">{current.label}</p>
      </div>
      {/* Desktop: full breadcrumbs. */}
      <nav aria-label="Breadcrumb" className="hidden min-w-0 lg:block">
        <ol className="flex min-w-0 items-center gap-1.5 text-sm">
          {crumbs.map((crumb, index) => (
            <li key={`${crumb.label}-${index}`} className="flex min-w-0 items-center gap-1.5">
              {index > 0 ? (
                <span aria-hidden className="text-subtle-foreground/60">
                  /
                </span>
              ) : null}
              {crumb.href ? (
                <Link
                  href={crumb.href}
                  className="max-w-[18rem] truncate rounded-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {crumb.label}
                </Link>
              ) : (
                <span aria-current="page" className="max-w-[24rem] truncate font-medium text-foreground">
                  {crumb.label}
                </span>
              )}
            </li>
          ))}
        </ol>
      </nav>
    </>
  );
}

function ActiveCrumbs() {
  const pathname = usePathname();
  return <Crumbs pathname={pathname} />;
}

function SearchTrigger() {
  const { openPalette } = useCommandPalette();
  const apple = useIsApple();
  return (
    <>
      <button
        type="button"
        onClick={openPalette}
        className="hidden h-9 w-60 cursor-pointer items-center gap-2 rounded-full border border-border bg-surface pr-1.5 pl-3 text-[13px] text-muted-foreground shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.05)] transition-colors hover:border-border-strong hover:text-foreground md:flex xl:w-72"
        aria-keyshortcuts={apple ? "Meta+K" : "Control+K"}
      >
        <Search className="size-4 shrink-0" aria-hidden />
        <span className="flex-1 truncate text-left">Search or jump to</span>
        <Kbd>{apple ? "⌘K" : "Ctrl K"}</Kbd>
      </button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={openPalette}
        className="text-muted-foreground hover:text-foreground md:hidden"
        aria-label="Search or jump to"
      >
        <Search />
      </Button>
    </>
  );
}

export function AdminTopBar() {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-xl">
      <div className="flex h-14 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0 flex-1">
          <Suspense fallback={<Crumbs pathname={null} />}>
            <ActiveCrumbs />
          </Suspense>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <SearchTrigger />
          <Button asChild variant="ghost" size="icon-sm" className="relative text-muted-foreground hover:text-foreground">
            <Link href="/admin/notifications" aria-label="Notifications, new items waiting">
              <Bell />
              <span aria-hidden className="absolute top-2 right-2 size-1.5 rounded-full bg-brand ring-2 ring-background" />
            </Link>
          </Button>
          <ThemeToggle />
          <LookPicker className="hidden sm:inline-flex" />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
