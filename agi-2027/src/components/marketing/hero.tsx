import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { StatusDot } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { brands, hero } from "@/lib/marketing-content";
import { BrandGlyph } from "./brand-glyph";
import { HeroObjects } from "./hero-objects";

function Hero() {
  return (
    // Pulled up under the floating header so the wall fills the screen.
    <section className="relative isolate -mt-[64px] overflow-hidden bg-wall sm:-mt-[68px]">
      <div className="mx-auto grid max-w-6xl items-center gap-x-6 gap-y-10 px-5 pt-32 sm:px-8 sm:pt-36 lg:min-h-[92svh] lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:pt-28">
        <div className="max-w-xl">
          <p className="inline-flex animate-fade-up items-center gap-2 text-[13px] font-medium text-muted-foreground">
            <StatusDot tone="brand" pulse className="size-2" />
            {hero.eyebrow}
          </p>
          <h1 className="mt-6 animate-fade-up text-display text-balance [animation-delay:60ms]">
            {hero.title[0]} {hero.title[1]}{" "}
            <em className="accent-serif">{hero.titleAccent}</em>.
          </h1>
          <p className="mt-6 max-w-md animate-fade-up text-[17px] leading-relaxed text-pretty text-muted-foreground [animation-delay:120ms]">
            {hero.lead}
          </p>
          <div className="mt-9 flex animate-fade-up flex-col gap-3 [animation-delay:180ms] sm:flex-row">
            <Button asChild>
              <Link href="/book">
                Book a campaign
                <ArrowRight />
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/apply">
                Apply as a creator
                <ArrowRight />
              </Link>
            </Button>
          </div>
        </div>
        <HeroObjects className="animate-fade-in [animation-delay:200ms]" />
      </div>

      <div className="mx-auto mt-8 max-w-6xl px-5 pb-10 sm:mt-4 sm:px-8 lg:mt-0">
        <p className="text-[13px] text-subtle-foreground">Trusted by teams shipping at the frontier of AI</p>
        <ul className="-mx-5 mt-4 flex snap-x gap-3 overflow-x-auto px-5 pb-2 [scrollbar-width:none] sm:mx-0 sm:grid sm:grid-cols-4 sm:overflow-visible sm:px-0 lg:grid-cols-8">
          {brands.map((brand, index) => (
            <li
              key={brand}
              className="flex h-14 shrink-0 snap-start items-center gap-2 rounded-xl border bg-surface/80 px-4 text-muted-foreground shadow-soft backdrop-blur-sm"
            >
              <BrandGlyph index={index} />
              <span className="text-[13px] font-semibold tracking-[-0.02em] whitespace-nowrap text-foreground/80">
                {brand}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export { Hero };
