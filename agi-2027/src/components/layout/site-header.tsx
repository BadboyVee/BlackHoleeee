"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu } from "lucide-react";

import { Wordmark } from "@/components/brand/wordmark";
import { LookPicker, useLook } from "@/components/theme/look-picker";
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

/**
 * Watches the marker the home page puts at the bottom of its hero. While the
 * hero is on screen the header floats over the art in white; past it, the
 * header turns solid. IntersectionObserver, never a scroll listener.
 */
function useOverHero(enabled: boolean) {
  const [overHero, setOverHero] = useState(enabled);
  // Each look has its own hero; follow the one that's showing.
  const look = useLook();
  useEffect(() => {
    if (!enabled) return;
    const marker = Array.from(document.querySelectorAll("[data-hero-end]")).find(
      (element) => element.getClientRects().length > 0,
    );
    if (!marker) return;
    const observer = new IntersectionObserver(
      ([entry]) => setOverHero(entry.boundingClientRect.top > 72),
      { threshold: [0, 1] },
    );
    observer.observe(marker);
    return () => observer.disconnect();
  }, [enabled, look]);
  return enabled && overHero;
}

/**
 * The public header. Each look has its own navigation style, copied from its
 * reference: Renaissance is a quiet row of links with a white pill, Agent is a
 * single comma-separated line with an underlined call to action, and Drop is
 * small caps with a chunky wordmark.
 */
function SiteHeader({ overlay = false }: { overlay?: boolean }) {
  const overHero = useOverHero(overlay);
  const tone = overHero ? "hero" : "solid";

  return (
    <header
      data-header-tone={tone}
      className={cn(
        "group/header inset-x-0 top-0 z-40 transition-[background-color,color,box-shadow,backdrop-filter] duration-300 ease-snap",
        overlay ? "fixed" : "sticky",
        tone === "hero"
          ? "bg-transparent text-white"
          : "border-b border-border bg-background/82 text-foreground backdrop-blur-xl supports-[backdrop-filter]:bg-background/70",
      )}
    >
      {/* Scrim so white text stays readable over bright parts of the art. */}
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute inset-x-0 top-0 -z-10 h-28 bg-linear-to-b from-black/35 to-transparent transition-opacity duration-300",
          tone === "hero" ? "opacity-100 agent:opacity-0 drop:opacity-40" : "opacity-0",
        )}
      />
      <div className="relative mx-auto flex h-16 max-w-[90rem] items-center gap-4 px-4 sm:px-6 lg:h-[4.5rem] lg:px-8">
        <Link href="/" aria-label="AGI 2027 home" className="pressable flex shrink-0 items-center">
          <Wordmark />
        </Link>

        {/* Renaissance: a quiet row of links next to the wordmark. */}
        <div className="look-renaissance">
          <nav aria-label="Main" className="ml-6 hidden lg:block">
          <ul className="flex items-center gap-1">
            {marketingNav.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="rounded-full px-3 py-2 text-[13px] font-semibold tracking-[-0.01em] opacity-90 transition-opacity hover:opacity-100 hover:underline hover:underline-offset-4"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          </nav>
        </div>

        {/* Agent: one comma-separated line, centred. */}
        <div className="look-agent">
          <nav aria-label="Main" className="absolute left-1/2 hidden -translate-x-1/2 lg:block">
          <p className="text-[14px] tracking-[-0.01em]">
            {marketingNav.map((link, index) => (
              <span key={link.href}>
                <Link href={link.href} className="decoration-1 underline-offset-4 hover:underline">
                  {link.label}
                </Link>
                {index < marketingNav.length - 1 ? ", " : null}
              </span>
            ))}
          </p>
          </nav>
        </div>

        {/* Drop: small caps, centred. */}
        <div className="look-drop">
          <nav aria-label="Main" className="absolute left-1/2 hidden -translate-x-1/2 lg:block">
          <ul className="flex items-center gap-7">
            {marketingNav.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="relative py-2 text-[12px] font-semibold tracking-[0.14em] uppercase after:absolute after:inset-x-0 after:bottom-0.5 after:h-0.5 after:origin-left after:scale-x-0 after:bg-current after:transition-transform after:duration-300 after:ease-snap hover:after:scale-x-100"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          </nav>
        </div>

        <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
          <LookPicker tone={tone === "hero" ? "hero" : "default"} className="max-sm:pr-1.5 max-sm:[&>span:last-child]:sr-only" />
          <ThemeToggle
            className={cn(
              "hidden sm:inline-flex",
              tone === "hero" && "text-white/85 hover:bg-white/15 hover:text-white",
            )}
          />

          <div className="look-renaissance">
            <Link
              href="/login"
              className="hidden px-2 text-[13px] font-semibold opacity-90 hover:opacity-100 hover:underline hover:underline-offset-4 md:inline"
            >
              Sign in
            </Link>
            <HeaderCta tone={tone} />
          </div>
          <div className="look-agent">
            <Link
              href="/book"
              className="hidden px-1 text-[14px] underline decoration-1 underline-offset-[5px] hover:decoration-2 md:inline"
            >
              Book a campaign
            </Link>
          </div>
          <div className="look-drop">
            <Link
              href="/login"
              className="hidden px-2 text-[12px] font-semibold tracking-[0.14em] uppercase md:inline"
            >
              Sign in
            </Link>
            <HeaderCta tone={tone} />
          </div>

          <MobileMenu tone={tone} />
        </div>
      </div>
    </header>
  );
}

function HeaderCta({ tone }: { tone: "hero" | "solid" }) {
  return (
    <Button
      asChild
      size="sm"
      className={cn(
        "hidden h-9 px-4 md:inline-flex",
        tone === "hero" && "bg-white text-[#141210] shadow-none hover:bg-white/90",
      )}
    >
      <Link href="/book">Book a campaign</Link>
    </Button>
  );
}

function MobileMenu({ tone }: { tone: "hero" | "solid" }) {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className={cn("lg:hidden", tone === "hero" ? "text-white hover:bg-white/15" : "text-foreground")}
          aria-label="Open menu"
        >
          <Menu className="size-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="gap-0 p-0">
        <SheetHeader className="h-16 justify-center border-b px-5 py-0">
          <SheetTitle className="flex items-center">
            <Wordmark />
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
        <div className="flex items-center justify-between border-t px-5 py-4">
          <span className="text-sm text-muted-foreground">Light or dark</span>
          <ThemeToggle />
        </div>
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
