import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";

import { Reveal, WordReveal } from "@/components/motion/reveal";
import { siteConfig } from "@/lib/site";

/**
 * The last word. Renaissance closes on Thomas Cole's storm breaking over the
 * Connecticut valley, Agent hands the mic back to Echo, Drop goes out on one
 * giant word.
 */
function FinalCtaSection() {
  const email = siteConfig.contactEmail;
  return (
    <section aria-label="Book a campaign" className="relative px-3 pt-10 pb-3 sm:px-5 sm:pb-5">
      {/* Renaissance */}
      <div className="look-renaissance">
        <div className="relative isolate mx-auto flex min-h-[78svh] max-w-[90rem] flex-col justify-end overflow-hidden rounded-[var(--radius-sm)] p-6 text-white sm:p-10 lg:p-14">
          <Image
            src="/art/oxbow-1900.webp"
            alt=""
            fill
            sizes="100vw"
            className="-z-10 object-cover object-[30%_50%] transition-transform duration-[2s] ease-snap"
          />
          <div aria-hidden className="absolute inset-0 -z-10 bg-linear-to-t from-black/70 via-black/20 to-black/10" />
          <WordReveal
            text="Your launch is next."
            className="max-w-[12ch] text-[clamp(2.75rem,1.6rem+5vw,6rem)] leading-[0.9] font-bold tracking-[-0.055em]"
          />
          <Reveal delay={0.15} className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              href="/book"
              className="pressable group inline-flex h-12 items-center gap-2 rounded-full bg-white px-6 text-[15px] font-semibold text-[#141210] transition-colors duration-300 ease-snap hover:bg-brand"
            >
              Book a campaign
              <ArrowRight className="size-4 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
            </Link>
            {email ? (
              <a href={`mailto:${email}`} className="inline-flex h-12 items-center gap-2 px-2 text-[15px] font-semibold underline-offset-4 hover:underline">
                <Mail className="size-4" />
                {email}
              </a>
            ) : null}
          </Reveal>
          <p className="mt-10 max-w-sm text-[11px] leading-snug text-white/70">
            Thomas Cole, View from Mount Holyoke, Northampton, Massachusetts, after a Thunderstorm (The Oxbow), 1836.
            The Met, public domain.
          </p>
        </div>
      </div>

      {/* Agent */}
      <div className="look-agent">
        <div className="texture-noise relative isolate mx-auto max-w-[90rem] overflow-hidden rounded-[2.5rem] bg-[radial-gradient(ellipse_80%_90%_at_70%_40%,#f0493c,#d92e24_50%,#b5170f)] px-6 py-16 text-white sm:px-12 sm:py-24">
          <div className="flex flex-col items-start gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="flex items-end gap-4">
              <Image
                src="/art/echo-avatar.webp"
                alt=""
                width={120}
                height={120}
                className="hidden size-28 shrink-0 animate-float rounded-full ring-4 ring-white/25 sm:block"
              />
              <div>
                <Reveal as="p" className="text-[clamp(1.125rem,1rem+0.4vw,1.375rem)] text-white/80">
                  Still here? Good sign.
                </Reveal>
                <WordReveal
                  text="So, what are we launching?"
                  className="mt-2 max-w-[16ch] text-[clamp(2.5rem,1.5rem+4.2vw,5.25rem)] leading-[0.95] font-medium tracking-[-0.05em]"
                />
              </div>
            </div>
            <Reveal delay={0.15} className="flex flex-wrap gap-2">
              <Link
                href="/book"
                className="pressable inline-flex h-12 items-center rounded-full bg-white px-6 text-[15px] font-medium text-[#1a1412] transition-colors hover:bg-[#1a1412] hover:text-white"
              >
                Book a campaign
              </Link>
              {email ? (
                <a
                  href={`mailto:${email}`}
                  className="pressable inline-flex h-12 items-center rounded-full px-6 text-[15px] font-medium ring-1 ring-white/80 transition-colors ring-inset hover:bg-white hover:text-[#1a1412]"
                >
                  Email {email}
                </a>
              ) : (
                <Link
                  href="/apply"
                  className="pressable inline-flex h-12 items-center rounded-full px-6 text-[15px] font-medium ring-1 ring-white/80 transition-colors ring-inset hover:bg-white hover:text-[#1a1412]"
                >
                  Apply as a creator
                </Link>
              )}
            </Reveal>
          </div>
        </div>
      </div>

      {/* Drop */}
      <div className="look-drop">
        <div className="relative isolate mx-auto max-w-[90rem] overflow-hidden rounded-[2.25rem] bg-block-1 px-6 pt-14 pb-10 text-white sm:px-12 sm:pt-20">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img src="/art/icons/bolt.webp" alt="" aria-hidden className="absolute top-5 right-5 w-14 rotate-12 animate-float drop-shadow-xl sm:top-8 sm:right-[8%] sm:w-28" />
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img src="/art/icons/heartwhite.webp" alt="" aria-hidden className="absolute bottom-24 left-[46%] hidden w-24 -rotate-12 animate-float drop-shadow-xl [animation-delay:-3s] sm:block" />
          <p className="text-[19px] font-semibold tracking-[-0.02em]">Got a launch coming?</p>
          <WordReveal
            text="Let's go."
            className="mt-2 font-[family-name:var(--font-anton)] text-[clamp(5rem,2rem+16vw,15rem)] leading-[0.85] font-normal tracking-[0.005em] uppercase"
          />
          <Reveal delay={0.15} className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/book"
              className="pressable inline-flex h-12 items-center gap-2 rounded-full bg-white px-6 text-[15px] font-semibold text-[#16120f] transition-transform duration-200 ease-snap hover:-translate-y-0.5"
            >
              Book a campaign
              <ArrowRight className="size-4" />
            </Link>
            {email ? (
              <a
                href={`mailto:${email}`}
                className="pressable inline-flex h-12 items-center gap-2 rounded-full px-6 text-[15px] font-semibold ring-1 ring-white/70 ring-inset hover:bg-white/15"
              >
                <Mail className="size-4" />
                {email}
              </a>
            ) : null}
          </Reveal>
        </div>
      </div>
    </section>
  );
}

export { FinalCtaSection };
