import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    // Pulled up under the transparent header so the glow reaches the top edge.
    <section className="relative isolate -mt-16 overflow-hidden pt-16 texture-noise">
      <div aria-hidden className="absolute inset-0 -z-10 bg-grid mask-fade-radial" />
      <div aria-hidden className="absolute inset-0 -z-10 bg-hero-glow" />

      <div className="mx-auto max-w-7xl px-4 pt-16 pb-24 sm:px-6 sm:pt-24 sm:pb-32 lg:px-8 lg:pt-32 lg:pb-40">
        <p className="inline-flex animate-fade-up items-center gap-2 rounded-full border border-border-strong bg-surface/60 px-3 py-1.5 text-label text-muted-foreground backdrop-blur">
          <span className="size-1.5 rounded-full bg-brand" aria-hidden />
          Creator marketing for AI launches
        </p>

        <h1 className="mt-7 max-w-[15ch] animate-fade-up text-display text-balance [animation-delay:80ms]">
          Your launch, everywhere your users scroll.
        </h1>

        <p className="mt-7 max-w-xl animate-fade-up text-lg text-pretty text-muted-foreground [animation-delay:160ms] sm:text-xl">
          We brief the AI and tech creators your future users already follow. They post on X when
          you launch, and you get a clear report on what it did.
        </p>

        <div className="mt-10 flex animate-fade-up flex-col gap-3 [animation-delay:240ms] sm:flex-row">
          <Button asChild variant="brand" size="xl">
            <Link href="/book">
              Book a campaign
              <ArrowRight />
            </Link>
          </Button>
          <Button asChild variant="secondary" size="xl">
            <Link href="/apply">Apply as a creator</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
