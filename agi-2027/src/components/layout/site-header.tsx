"use client";

import { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { ArrowRight, Menu } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { marketingNav } from "@/lib/nav";

function subscribeToScroll(onChange: () => void) {
  window.addEventListener("scroll", onChange, { passive: true });
  return () => window.removeEventListener("scroll", onChange);
}

function SiteHeader() {
  const scrolled = useSyncExternalStore(
    subscribeToScroll,
    () => window.scrollY > 8,
    () => false,
  );

  return (
    <header
      data-scrolled={scrolled}
      className="sticky top-0 z-40 border-b border-transparent transition-[background-color,border-color] duration-300 data-[scrolled=true]:border-border data-[scrolled=true]:bg-background/75 data-[scrolled=true]:backdrop-blur-xl"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" aria-label="AGI 2027 home" className="shrink-0">
          <Logo />
        </Link>

        <nav aria-label="Main" className="mx-auto hidden items-center gap-0.5 md:flex">
          {marketingNav.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3.5 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-1.5 md:ml-0">
          <ThemeToggle />
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild variant="brand" size="sm" className="hidden sm:inline-flex">
            <Link href="/book">Book a campaign</Link>
          </Button>
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
        <Button variant="ghost" size="icon-sm" className="md:hidden" aria-label="Open menu">
          <Menu className="size-5" />
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
          {marketingNav.map((link) => (
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
            <Button asChild variant="brand" size="lg">
              <Link href="/book">Book a campaign</Link>
            </Button>
          </SheetClose>
          <SheetClose asChild>
            <Button asChild variant="secondary" size="lg">
              <Link href="/apply">Apply as a creator</Link>
            </Button>
          </SheetClose>
          <SheetClose asChild>
            <Button asChild variant="ghost" size="lg">
              <Link href="/login">Sign in</Link>
            </Button>
          </SheetClose>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export { SiteHeader };
