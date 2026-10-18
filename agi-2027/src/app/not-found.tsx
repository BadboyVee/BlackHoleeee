import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = { title: "Page not found" };

/** 404, told in the voice of the active look. */
export default function NotFound() {
  return (
    <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-hidden px-4 py-16 text-center">
      <Link href="/" aria-label="AGI 2027 home" className="mb-10">
        <Wordmark />
      </Link>

      <div className="look-renaissance">
        <div className="relative mb-8 aspect-[4/3] w-full max-w-sm overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-8 ring-surface">
          <Image
            src="/art/detail-hand.webp"
            alt="Orion reaching into the distance, a detail from Poussin's painting"
            fill
            sizes="384px"
            className="object-cover"
          />
        </div>
      </div>
      <div className="look-agent">
        <Image src="/art/echo-avatar.webp" alt="" width={120} height={120} className="mb-6 size-28 animate-float" />
      </div>
      <div className="look-drop">
        <p
          aria-hidden
          className="mb-2 font-[family-name:var(--font-anton)] text-[clamp(7rem,30vw,16rem)] leading-[0.85] text-brand-text"
        >
          404
        </p>
      </div>

      <p className="text-sm font-semibold text-subtle-foreground drop:hidden">404</p>
      <h1 className="mt-3 text-h1 text-balance">This page doesn&apos;t exist.</h1>
      <p className="mt-4 max-w-md text-pretty text-muted-foreground">
        The link may be old or mistyped. Head back home, or apply to join as a creator.
      </p>
      <div className="mt-9 flex flex-col gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/">
            <ArrowLeft />
            Back home
          </Link>
        </Button>
        <Button asChild variant="secondary" size="lg">
          <Link href="/apply">Apply as a creator</Link>
        </Button>
      </div>
    </main>
  );
}
