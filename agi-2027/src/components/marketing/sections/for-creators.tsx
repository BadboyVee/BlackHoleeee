import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BadgeDollarSign, Bell, Wand2 } from "lucide-react";

import { Reveal, RevealGroup, RevealItem } from "@/components/motion/reveal";
import { cn } from "@/lib/utils";
import { ClaimPreview } from "./claim-preview";
import { GuidePreview } from "./guide-preview";
import { EchoSays, SectionTitle } from "./shared";

const perks = [
  {
    icon: Bell,
    title: "Claim what you like",
    body: "New drops land in your portal and on Telegram. Tap Claim and the slot is yours.",
  },
  {
    icon: Wand2,
    title: "Clear briefs, your angle",
    body: "The brief, your own angle, the assets and the exact post window, all in one place.",
  },
  {
    icon: BadgeDollarSign,
    title: "Paid per post",
    body: "Once your proof is approved you see the earning, then the payment with its reference.",
  },
];

/**
 * The creator pitch, with two phones: Jesse claiming a real campaign in one
 * tap, and a guide to how it all works. Renaissance hangs them in front of a
 * detail of Claude Lorrain's sunrise, Agent sets them side by side on a soft
 * card, Drop fans them out like stickers.
 */
function ForCreatorsSection() {
  return (
    <section
      id="creators"
      aria-label="For creators"
      className="relative scroll-mt-20 overflow-hidden py-20 sm:py-28 drop:bg-block-3 drop:text-white"
    >
      <div className="mx-auto grid max-w-[84rem] items-center gap-14 px-5 sm:px-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-16 lg:px-10">
        <div>
          <EchoSays>Are you a creator? This part&apos;s for you.</EchoSays>
          <SectionTitle
            title="Get paid to post about launches you'd talk about anyway."
            lead="Join a network of builders, writers and video makers who post about AI on X."
            className="[&_p]:drop:text-white/85"
          />
          <RevealGroup as="ul" className="mt-10 grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            {perks.map(({ icon: Icon, title, body }) => (
              <RevealItem
                as="li"
                key={title}
                className={cn(
                  "rounded-[var(--radius-lg)] bg-surface p-5 shadow-soft ring-1 ring-border",
                  "renaissance:bg-surface/90",
                  "drop:bg-white/12 drop:shadow-none drop:ring-white/20",
                )}
              >
                <Icon className="size-5 text-brand-text drop:text-[#ffd23f]" aria-hidden />
                <p className="mt-3 text-[15px] font-semibold tracking-[-0.015em]">{title}</p>
                <p className="mt-1 text-[14px] leading-relaxed text-muted-foreground drop:text-white/85">{body}</p>
              </RevealItem>
            ))}
          </RevealGroup>
          <Reveal className="mt-10 flex flex-col gap-3 sm:flex-row" delay={0.1}>
            <Link
              href="/apply"
              className="pressable inline-flex h-12 items-center justify-center gap-2 rounded-full bg-foreground px-6 text-[15px] font-semibold text-background transition-transform duration-200 ease-snap hover:-translate-y-0.5 agent:bg-brand agent:text-brand-foreground drop:bg-white drop:text-[#16120f]"
            >
              Apply as a creator
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/login"
              className="pressable inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-[15px] font-semibold ring-1 ring-border-strong transition-colors duration-200 ease-snap ring-inset hover:bg-surface-2 drop:ring-white/60 drop:hover:bg-white/10"
            >
              Already a creator? Sign in
            </Link>
          </Reveal>
        </div>

        <div className="min-w-0">
          <div className="look-renaissance">
            <figure className="relative mx-auto w-full max-w-[34rem] lg:max-w-none">
              <Reveal className="relative">
                <div className="relative aspect-[4/5] overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-[10px] ring-surface">
                  <Image
                    src="/art/detail-trees.webp"
                    alt="Trees catching the first light, a detail of Claude Lorrain's Sunrise"
                    fill
                    sizes="(min-width: 1024px) 40vw, (min-width: 640px) 34rem, 100vw"
                    className="object-cover transition-transform duration-[1.4s] ease-snap hover:scale-105"
                  />
                </div>
                {/* The guide hangs high on the right, the drop low on the left, both over the frame. */}
                <Reveal
                  delay={0.12}
                  className="absolute top-[18%] -right-1.5 z-10 [--phone-scale:0.6] sm:top-[8%] sm:-right-10 sm:[--phone-scale:0.8] lg:-right-4 lg:[--phone-scale:0.62] xl:-right-4 xl:[--phone-scale:0.8]"
                >
                  <GuidePreview />
                </Reveal>
                <Reveal
                  delay={0.2}
                  className="absolute -bottom-[96px] -left-1.5 z-20 [--phone-scale:0.6] sm:-bottom-16 sm:-left-10 sm:[--phone-scale:0.8] lg:-bottom-10 lg:-left-6 lg:[--phone-scale:0.62] xl:-bottom-12 xl:-left-8 xl:[--phone-scale:0.8]"
                >
                  <ClaimPreview />
                </Reveal>
              </Reveal>
              {/* A wall label, beside the phone that hangs below the frame. */}
              <figcaption className="mt-12 ml-auto w-[48%] text-right text-xs leading-relaxed text-pretty text-subtle-foreground sm:mt-3 sm:w-[56%] lg:w-[58%]">
                Detail, Claude Lorrain, Sunrise, about 1646 to 1647. The Met, public domain.
              </figcaption>
            </figure>
          </div>

          <div className="look-agent">
            <Reveal className="relative isolate -mx-2 overflow-hidden rounded-[2.5rem] bg-surface px-2.5 pt-8 pb-12 shadow-soft ring-1 ring-border sm:mx-0 sm:px-8 sm:pt-12 sm:pb-16">
              <div
                aria-hidden
                className="absolute inset-0 -z-10 bg-[radial-gradient(60%_50%_at_30%_35%,var(--glow),transparent_70%),radial-gradient(50%_45%_at_75%_70%,var(--glow),transparent_70%)]"
              />
              <div className="flex items-start justify-center gap-1.5 sm:gap-8 lg:gap-5 xl:gap-8">
                <ClaimPreview className="[--phone-scale:0.58] sm:[--phone-scale:0.9] lg:[--phone-scale:0.64] xl:[--phone-scale:0.8]" />
                <GuidePreview className="mt-10 [--phone-scale:0.58] sm:mt-16 sm:[--phone-scale:0.9] lg:mt-12 lg:[--phone-scale:0.64] xl:mt-16 xl:[--phone-scale:0.8]" />
              </div>
            </Reveal>
          </div>

          <div className="look-drop">
            {/* items-start: stretched, the second sticker's white backing would run past its phone. */}
            <Reveal className="relative -mx-2 flex items-start justify-center pt-6 pb-12 sm:mx-0 sm:pt-10">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img src="/art/icons/sparklime.webp" alt="" aria-hidden className="absolute top-0 left-[2%] z-30 w-16 animate-float drop-shadow-xl sm:-top-4 sm:left-[6%] sm:w-24" />
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img src="/art/icons/heart.webp" alt="" aria-hidden className="absolute -right-1 bottom-0 z-30 w-16 animate-float drop-shadow-xl [animation-delay:-2s] sm:right-[2%] sm:bottom-2 sm:w-24" />
              <div className="relative z-20 mt-10 -rotate-[4deg] rounded-[calc(45.6px*var(--phone-scale)+6px)] bg-white p-1.5 shadow-[0_30px_60px_-20px_rgb(0_0_0/0.45)] [--phone-scale:0.52] sm:mt-14 sm:mr-4 sm:-rotate-6 sm:[--phone-scale:0.86] lg:mr-2 lg:[--phone-scale:0.6] xl:mr-4 xl:[--phone-scale:0.76]">
                <ClaimPreview />
              </div>
              <div className="relative z-10 rotate-[4deg] rounded-[calc(45.6px*var(--phone-scale)+6px)] bg-white p-1.5 shadow-[0_30px_60px_-20px_rgb(0_0_0/0.45)] [--phone-scale:0.52] sm:rotate-[5deg] sm:[--phone-scale:0.86] lg:[--phone-scale:0.6] xl:[--phone-scale:0.76]">
                <GuidePreview />
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

export { ForCreatorsSection };
