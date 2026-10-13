"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Bell, ChevronLeft, LogIn, RotateCcw, ShieldCheck, UserRound } from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { useAccount } from "@/components/auth/account-context";
import { SignOutMenuItem } from "@/components/auth/sign-out";
import { LookPicker } from "@/components/theme/look-picker";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import type { Account } from "@/lib/auth/account-display";
import { isStaff } from "@/lib/auth/routes";
import type { CreatorMe } from "@/lib/campaigns/demo-creator";
import { cn } from "@/lib/utils";

import { resetDemoClaims } from "./claim-store";
import { useCreatorDemo } from "./creator-data";
import { isCampaignPage } from "./creator-nav";
import { useHydrated } from "./hooks";
import { NotificationDot, useNotifications } from "./notifications";
import { pressed, springArrive } from "./motion";

/** Small, honest note that everything here is sample data. */
export function DemoNote({ className }: { className?: string }) {
  return (
    <span
      data-tone="amber"
      className={cn("inline-flex items-center gap-1.5 text-xs leading-none text-muted-foreground", className)}
    >
      <span aria-hidden className="size-1.5 shrink-0 rounded-full bg-(--tone-fg)" />
      Preview with demo data
    </span>
  );
}

/** Who the top bar shows: the signed-in account, or the demo creator on a preview without Supabase. */
type Person = { name: string; firstName: string; initials: string; detail: string };

function personFrom(account: Account | null, me: CreatorMe): Person {
  return account
    ? { name: account.name, firstName: account.firstName, initials: account.initials, detail: account.email }
    : { name: me.name, firstName: me.firstName, initials: me.initials, detail: `${me.handle} · ${me.tier}` };
}

function AvatarMenu({ person, account }: { person: Person; account: Account | null }) {
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <motion.button
          type="button"
          whileTap={pressed}
          aria-label={`Your account, ${person.name}`}
          className="relative flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full outline-none"
        >
          <span className="flex size-10 items-center justify-center rounded-full bg-foreground font-mono text-[13px] font-semibold tracking-tight text-background shadow-[inset_0_1px_0_rgb(255_255_255/0.18),0_4px_12px_-4px_rgb(var(--shadow-rgb)/0.45)]">
            {person.initials}
          </span>
          <span aria-hidden className="absolute right-0.5 bottom-0.5 size-3 rounded-full border-2 border-background bg-(--tone-green)" />
        </motion.button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-72">
        <DropdownMenuLabel className="flex flex-col gap-1 pb-2.5">
          <span className="truncate text-[15px] font-semibold">{person.name}</span>
          <span className="truncate text-xs font-normal text-muted-foreground">{person.detail}</span>
          <DemoNote className="mt-1.5" />
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/dashboard/profile">
            <UserRound />
            Your profile
          </Link>
        </DropdownMenuItem>
        {!account || isStaff(account.role) ? (
          <DropdownMenuItem asChild>
            <Link href="/admin">
              <ShieldCheck />
              Switch to the owner view
            </Link>
          </DropdownMenuItem>
        ) : null}
        <DropdownMenuItem asChild>
          <Link href="/">
            <ArrowUpRight />
            Public site
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={() => {
            resetDemoClaims();
            toast.success("Demo reset", { description: "Claims are back to how the demo started." });
          }}
        >
          <RotateCcw />
          Reset the demo
        </DropdownMenuItem>
        {account ? (
          <SignOutMenuItem />
        ) : (
          <DropdownMenuItem asChild>
            <Link href="/login">
              <LogIn />
              Sign in
            </Link>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** Avatar and a hello. Home has its own big greeting, so the bar shows your name there instead. */
function Greeting({ home = false }: { home?: boolean }) {
  return (
    <Suspense fallback={<GreetingSkeleton />}>
      <AccountGreeting home={home} />
    </Suspense>
  );
}

function AccountGreeting({ home }: { home: boolean }) {
  const { me } = useCreatorDemo();
  const account = useAccount();
  const person = personFrom(account, me);
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <AvatarMenu person={person} account={account} />
      <div className="min-w-0">
        <p className="truncate text-[15px] leading-tight font-semibold tracking-[-0.02em]">
          {home ? person.name : `Hey, ${person.firstName}`}
        </p>
        <DemoNote className="mt-1 whitespace-nowrap" />
      </div>
    </div>
  );
}

/** While the account loads: the avatar's place and a line for the name. */
function GreetingSkeleton() {
  return (
    <div className="flex min-w-0 items-center gap-2.5" aria-hidden>
      <span className="flex size-11 shrink-0 items-center justify-center">
        <Skeleton className="size-10 rounded-full" />
      </span>
      <div className="grid min-w-0 gap-1.5">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-3 w-36" />
      </div>
    </div>
  );
}

function BackToCampaigns() {
  return (
    <motion.div whileTap={pressed} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={springArrive}>
      <Link
        href="/dashboard/campaigns"
        className="-ml-2 inline-flex h-11 items-center gap-1 rounded-full pr-3.5 pl-2 text-[15px] font-medium transition-colors hover:bg-surface-2"
      >
        <ChevronLeft className="size-5" />
        Campaigns
      </Link>
    </motion.div>
  );
}

function LeftSide() {
  const pathname = usePathname();
  return isCampaignPage(pathname) ? <BackToCampaigns /> : <Greeting home={pathname === "/dashboard"} />;
}

function NotificationsBell() {
  const { unread } = useNotifications();
  const hydrated = useHydrated();
  return (
    <motion.div whileTap={pressed}>
      <Link
        href="/dashboard/notifications"
        aria-label={hydrated && unread ? `Notifications, ${unread} new` : "Notifications"}
        className="relative inline-flex size-11 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground sm:size-10"
      >
        <Bell className="size-[19px]" />
        <NotificationDot className="top-2 right-2 sm:top-1.5 sm:right-1.5" />
      </Link>
    </motion.div>
  );
}

/**
 * The creator app's top bar: who you are on the left (a back button on a
 * campaign page), look, mode and notifications on the right. It gains a hairline
 * once the page scrolls, watched with an observer instead of scroll events.
 */
function CreatorTopBar() {
  const sentinel = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const node = sentinel.current;
    if (!node) return;
    const observer = new IntersectionObserver(([entry]) => setScrolled(!entry.isIntersecting));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div ref={sentinel} aria-hidden className="pointer-events-none absolute top-0 h-px w-px" />
      <header
        className={cn(
          "sticky top-0 z-30 border-b backdrop-blur-xl backdrop-saturate-150 transition-[background-color,border-color,box-shadow] duration-300",
          scrolled
            ? "border-border bg-background/80 shadow-[0_8px_24px_-18px_rgb(var(--shadow-rgb)/0.5)]"
            : "border-transparent bg-background/40",
        )}
      >
        <div className="mx-auto flex h-[4.25rem] w-full max-w-[68rem] items-center gap-2 px-4 pt-[env(safe-area-inset-top)] sm:h-[4.5rem] sm:px-6 lg:px-10">
          <div className="min-w-0 flex-1">
            <Suspense fallback={<GreetingSkeleton />}>
              <LeftSide />
            </Suspense>
          </div>
          <div className="flex shrink-0 items-center gap-0.5 sm:gap-1">
            <LookPicker className="mr-0.5 h-10 max-sm:w-10 max-sm:justify-center max-sm:px-0 sm:mr-1.5 max-sm:[&>span:last-child]:hidden" />
            <ThemeToggle className="size-11 sm:size-10" />
            <NotificationsBell />
          </div>
        </div>
      </header>
    </>
  );
}

export { CreatorTopBar };
