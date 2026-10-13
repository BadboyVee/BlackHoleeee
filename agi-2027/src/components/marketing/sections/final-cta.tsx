import Image from "next/image";
import { Mail } from "lucide-react";

import { BookForm } from "@/components/marketing/book-form";
import { Reveal, WordReveal } from "@/components/motion/reveal";
import { siteConfig } from "@/lib/site";
import { cn } from "@/lib/utils";

/**
 * The last word, with the booking form right there. Renaissance closes on
 * Thomas Cole's storm breaking over the Connecticut valley, Agent hands the
 * mic back to Echo, Drop goes out on one giant word. The form sits on the
 * block in a card: beside the headline on wide screens, under it on phones.
 * One form serves every look, so a half-filled form survives a look switch.
 */
function FinalCtaSection() {
  const email = siteConfig.contactEmail;
  return (
    <section id="book" aria-label="Book a campaign" className="relative scroll-mt-20 px-3 pt-10 pb-3 sm:px-5 sm:pb-5">
      <div
        className={cn(
          "relative isolate mx-auto grid max-w-[90rem] gap-8 overflow-hidden text-white",
          "lg:grid-cols-[minmax(0,1fr)_minmax(0,30rem)] lg:gap-10 xl:grid-cols-[minmax(0,1fr)_minmax(0,37rem)] xl:gap-16",
          // Renaissance: the painting, then forest green under the card on phones.
          "renaissance:rounded-[var(--radius-sm)] renaissance:bg-block-1 renaissance:p-6 renaissance:sm:p-10 renaissance:lg:p-14",
          // Agent: the warm red field.
          "agent:texture-noise agent:rounded-[2.5rem] agent:bg-[radial-gradient(ellipse_80%_90%_at_70%_40%,#f0493c,#d92e24_50%,#b5170f)] agent:px-5 agent:py-12 agent:sm:px-12 agent:sm:py-16 agent:lg:py-20",
          // Drop: one juicy block.
          "drop:rounded-[2.25rem] drop:bg-block-1 drop:px-5 drop:pt-14 drop:pb-5 drop:sm:px-12 drop:sm:pt-20 drop:sm:pb-12",
        )}
      >
        <div className="look-renaissance">
          <div aria-hidden className="absolute inset-x-0 top-0 -z-10 h-[34rem] lg:inset-y-0 lg:h-auto">
            <Image
              src="/art/oxbow-1900.webp"
              alt=""
              fill
              sizes="100vw"
              className="object-cover object-[30%_50%]"
            />
            <div className="absolute inset-0 bg-linear-to-t from-black/70 via-black/20 to-black/10" />
            <div className="absolute inset-x-0 bottom-0 h-24 bg-linear-to-b from-transparent to-block-1 lg:hidden" />
          </div>
        </div>

        {/* The headline, in each look's voice. */}
        <div
          className={cn(
            "@container relative flex min-w-0 flex-col",
            "renaissance:min-h-[26rem] renaissance:justify-end renaissance:sm:min-h-[27rem] renaissance:lg:min-h-0",
            "agent:lg:justify-center drop:lg:justify-end",
          )}
        >
          <div className="look-renaissance">
            <WordReveal
              text="Your launch is next."
              className="max-w-[12ch] text-[clamp(2.75rem,1.6rem+5vw,6rem)] leading-[0.9] font-bold tracking-[-0.055em]"
            />
            <Reveal as="p" delay={0.1} className="mt-5 max-w-sm text-[17px] leading-snug text-white/85">
              Tell us what you&apos;re shipping. We&apos;ll find the creators who can carry it.
            </Reveal>
          </div>

          <div className="look-agent">
            <div className="flex items-end gap-4">
              <Image
                src="/art/echo-avatar.webp"
                alt=""
                width={120}
                height={120}
                className="hidden size-24 shrink-0 animate-float rounded-full ring-4 ring-white/25 sm:block xl:size-28"
              />
              <div className="min-w-0">
                <Reveal as="p" className="text-[clamp(1.125rem,1rem+0.4vw,1.375rem)] text-white/80">
                  Still here? Good sign.
                </Reveal>
                <WordReveal
                  text="So, what are we launching?"
                  className="mt-2 max-w-[14ch] text-[clamp(2.5rem,1.5rem+3.6vw,4.75rem)] leading-[0.95] font-medium tracking-[-0.05em]"
                />
              </div>
            </div>
            <Reveal as="p" delay={0.1} className="mt-6 max-w-sm text-[17px] leading-snug text-white/85 sm:ml-28 xl:ml-32">
              Fill this in and I&apos;ll get it to the team. A person replies within one working day.
            </Reveal>
          </div>

          <div className="look-drop">
            {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
            <img
              src="/art/icons/bolt.webp"
              alt=""
              aria-hidden
              className="pointer-events-none absolute -top-8 right-0 w-14 rotate-12 animate-float drop-shadow-xl sm:-top-10 sm:w-24 lg:top-[6%] lg:right-auto lg:left-[8%] lg:w-32"
            />
            {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
            <img
              src="/art/icons/heartwhite.webp"
              alt=""
              aria-hidden
              className="pointer-events-none absolute top-[24%] left-[52%] hidden w-24 -rotate-12 animate-float drop-shadow-xl [animation-delay:-3s] lg:block"
            />
            <p className="text-[19px] font-semibold tracking-[-0.02em]">Got a launch coming?</p>
            <WordReveal
              text="Let's go."
              className="mt-4 font-[family-name:var(--font-anton)] text-[clamp(5rem,34cqi,15rem)] leading-[0.85] font-normal tracking-[0.005em] uppercase"
            />
          </div>

          {email ? (
            <Reveal delay={0.15} className="mt-8 agent:sm:ml-28 agent:xl:ml-32">
              <a
                href={`mailto:${email}`}
                className={cn(
                  "pressable inline-flex h-12 max-w-full items-center gap-2 text-[15px] font-semibold",
                  "renaissance:underline-offset-4 renaissance:hover:underline",
                  "agent:rounded-full agent:px-6 agent:font-medium agent:ring-1 agent:ring-white/80 agent:transition-colors agent:ring-inset agent:hover:bg-white agent:hover:text-[#1a1412]",
                  "drop:rounded-full drop:px-6 drop:ring-1 drop:ring-white/70 drop:ring-inset drop:hover:bg-white/15",
                )}
              >
                <Mail className="size-4 shrink-0" aria-hidden />
                <span className="truncate">{email}</span>
              </a>
            </Reveal>
          ) : null}

          <p className="look-renaissance">
            <span className="mt-8 block max-w-sm text-[11px] leading-snug text-white/70 lg:mt-12">
              Thomas Cole, View from Mount Holyoke, Northampton, Massachusetts, after a Thunderstorm (The Oxbow), 1836.
              The Met, public domain.
            </span>
          </p>
        </div>

        {/* The form, on a calm card. */}
        <Reveal delay={0.1} y={32} className="min-w-0 lg:self-start">
          <div className="rounded-[var(--radius-xl)] bg-surface p-5 text-foreground shadow-float sm:p-8">
            <BookForm
              source="home_cta"
              variant="compact"
              title="Book a campaign"
              intro="Tell us what you're launching and when."
            />
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export { FinalCtaSection };
