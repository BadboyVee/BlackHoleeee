import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BadgeDollarSign, Bell, Wand2 } from "lucide-react";

import { Reveal, RevealGroup, RevealItem } from "@/components/motion/reveal";
import { cn } from "@/lib/utils";
import { ClaimPreview } from "./claim-preview";
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
 * The creator pitch, with a phone where a creator claims a campaign in one
 * tap. Renaissance hangs it in front of a detail of Claude Lorrain's sunrise.
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

        <div>
          <div className="look-renaissance">
            <Reveal>
              <figure className="relative">
                <div className="relative aspect-[4/5] overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-[10px] ring-surface">
                  <Image
                    src="/art/detail-trees.webp"
                    alt="Trees catching the first light, a detail of Claude Lorrain's Sunrise"
                    fill
                    sizes="(min-width: 1024px) 40vw, 100vw"
                    className="object-cover transition-transform duration-[1.4s] ease-snap hover:scale-105"
                  />
                </div>
                <figcaption className="mt-3 text-xs text-subtle-foreground">
                  Detail, Claude Lorrain, Sunrise, about 1646 to 1647. The Met, public domain.
                </figcaption>
                <div className="absolute -bottom-6 -left-4 w-[62%] sm:-left-10">
                  <ClaimPreview className="origin-bottom-left scale-[0.62] sm:scale-75" />
                </div>
              </figure>
            </Reveal>
          </div>
          <div className="look-agent">
            <Reveal>
              <ClaimPreview />
            </Reveal>
          </div>
          <div className="look-drop">
            <Reveal className="relative">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img src="/art/icons/sparklime.webp" alt="" aria-hidden className="absolute -top-6 left-[8%] z-10 w-20 animate-float drop-shadow-xl sm:w-24" />
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img src="/art/icons/heart.webp" alt="" aria-hidden className="absolute right-[6%] bottom-10 z-10 w-24 animate-float drop-shadow-xl [animation-delay:-2s] sm:w-28" />
              <ClaimPreview />
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

export { ForCreatorsSection };
