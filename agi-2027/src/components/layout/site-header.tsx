"use client";

import { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { ArrowRight, Menu } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { marketingNav } from "@/lib/nav";
import { cn } from "@/lib/utils";

function subscribeToScroll(onChange: () => void) {
  window.addEventListener("scroll", onChange, { passive: true });
  return () => window.removeEventListener("scroll", onChange);
}

const pill =
  "border border-border bg-surface/80 shadow-soft backdrop-blur-xl supports-[backdrop-filter]:bg-surface/65";

/** Floating header: the logo in a chip on the left, navigation in a pill on the right. */
function SiteHeader() {
  const scrolled = useSyncExternalStore(
    subscribeToScroll,
    () => window.scrollY > 8,
    () => false,
  );

  return (
    <header data-scrolled={scrolled} className="sticky top-0 z-40 px-3 pt-3 sm:px-5 sm:pt-4">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between gap-3">
        <Link
          href="/"
          aria-label="AGI 2027 home"
          className={cn("flex h-11 items-center rounded-[14px] px-3.5 transition-shadow", pill)}
        >
          <Logo />
        </Link>

        <nav aria-label="Main" className={cn("hidden h-11 items-center gap-0.5 rounded-full p-1 md:flex", pill)}>
          {marketingNav.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3.5 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-surface-3/70 hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/login"
            className="rounded-full px-3.5 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-surface-3/70 hover:text-foreground"
          >
            Sign in
          </Link>
          <ThemeToggle className="size-9" />
          <Button asChild size="sm" className="h-9 px-4">
            <Link href="/book">
              Book a campaign
              <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        </nav>

        <div className={cn("flex h-11 items-center gap-0.5 rounded-full p-1 md:hidden", pill)}>
          <ThemeToggle className="size-9" />
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}

function MobileMenu() {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon-sm" className="text-foreground" aria-label="Open menu">
          <Menu className="size-[18px]" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="gap-0 p-0">
        <SheetHeader className="h-16 justify-center border-b px-5 py-0">
          <SheetTitle>
            <Logo />
          </SheetTitle>
          <SheetDescription className="sr-only">Site navigation</SheetDescription>
        </SheetHeader>
        <nav aria-label="Mobile" className="flex flex-col p-3">
          {[...marketingNav, { href: "/login", label: "Sign in" }].map((link) => (
            <SheetClose asChild key={link.href}>
              <Link
                href={link.href}
                className="flex min-h-12 items-center justify-between rounded-xl px-3 text-[17px] font-medium tracking-tight transition-colors hover:bg-surface-2"
              >
                {link.label}
                <ArrowRight className="size-4 text-subtle-foreground" />
              </Link>
            </SheetClose>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-2.5 border-t p-5">
          <SheetClose asChild>
            <Button asChild size="lg">
              <Link href="/book">Book a campaign</Link>
            </Button>
          </SheetClose>
          <SheetClose asChild>
            <Button asChild variant="secondary" size="lg">
              <Link href="/apply">Apply as a creator</Link>
            </Button>
          </SheetClose>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export { SiteHeader };
