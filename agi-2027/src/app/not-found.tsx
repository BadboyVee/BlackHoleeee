import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-hidden px-4 text-center texture-noise">
      <div aria-hidden className="absolute inset-0 -z-10 bg-grid mask-fade-radial" />
      <div
        aria-hidden
        className="absolute top-1/2 left-1/2 -z-10 h-96 w-[40rem] -translate-1/2 rounded-full bg-(--glow) blur-[120px]"
      />
      <Link href="/" aria-label="AGI 2027 home" className="mb-12">
        <Logo />
      </Link>
      <p className="font-mono text-sm tracking-[0.3em] text-brand-text">404</p>
      <h1 className="mt-4 text-h1 text-balance">This page doesn&apos;t exist.</h1>
      <p className="mt-4 max-w-md text-pretty text-muted-foreground">
        The link may be old or mistyped. Head back home, or browse the campaigns that are open
        right now.
      </p>
      <div className="mt-9 flex flex-col gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/">
            <ArrowLeft />
            Back home
          </Link>
        </Button>
        <Button asChild variant="secondary" size="lg">
          <Link href="/campaigns">Open campaigns</Link>
        </Button>
      </div>
    </main>
  );
}
