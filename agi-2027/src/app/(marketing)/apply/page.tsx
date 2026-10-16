import type { Metadata } from "next";
import Image from "next/image";
import { MessagesSquare, PenLine, Ticket, UsersRound } from "lucide-react";

import { MarketingMain } from "@/components/layout/marketing-main";
import { ApplyCta } from "@/components/marketing/apply-cta";
import { EchoSays, SectionShell, SectionTitle } from "@/components/marketing/sections/shared";
import { Reveal, RevealGroup, RevealItem, RuleDraw, WordReveal } from "@/components/motion/reveal";
import { cn } from "@/lib/utils";

const DESCRIPTION = "Get paid to post about the most interesting launches in AI and tech.";

export const metadata: Metadata = {
  title: "Apply as a creator",
  description: DESCRIPTION,
  alternates: { canonical: "/apply" },
};

const STEPS = [
  {
    title: "Apply",
    body: "About five minutes. Tell us about your audience and share your three best posts.",
  },
  {
    title: "We review",
    body: "A person reads every application, usually within a few days. We email you the answer.",
  },
  {
    title: "Claim campaigns",
    body: "Once you're in, campaigns open to you appear in your dashboard. Claim the ones you like.",
  },
  {
    title: "Post and get paid",
    body: "Follow the brief and post on X. Once your post is approved, we pay you in USDC or USDT on Base, Solana and other networks, or by bank transfer.",
  },
];

const LOOK_FOR = [
  {
    icon: UsersRound,
    title: "An audience that cares",
    body: "People who follow you for AI, tech, crypto or startups.",
  },
  {
    icon: MessagesSquare,
    title: "Posts people reply to",
    body: "Real conversation under your posts, not just views.",
  },
  {
    icon: PenLine,
    title: "Your own voice",
    body: "Posts that sound like you. The brief gives you the facts, the angle is yours.",
  },
];

const DROP_BLOCKS = ["drop:bg-block-1", "drop:bg-block-4", "drop:bg-block-3", "drop:bg-block-5"];

/**
 * The creator pitch. Fully prerendered: the only thing read from the address
 * is a referral code, and the calls to action read that in the browser.
 */
export default function ApplyPage() {
  return (
    <MarketingMain>
      <ApplyHero />
      <HowItWorks />
      <WhatWeLookFor />
      <ClosingCta />
    </MarketingMain>
  );
}

/** Title, lead and the two ways in, in each look's voice. */
function ApplyHero() {
  return (
    <section aria-labelledby="apply-title" className="drop:px-3 drop:pt-3 drop:sm:px-5 drop:sm:pt-5">
      <div
        className={cn(
          "relative isolate mx-auto max-w-[84rem] px-5 pt-12 sm:px-8 sm:pt-16 lg:px-10",
          "renaissance:grid renaissance:items-center renaissance:gap-10 renaissance:lg:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] renaissance:xl:gap-16",
          "drop:max-w-[90rem] drop:overflow-hidden drop:rounded-[2.25rem] drop:bg-block-1 drop:px-6 drop:pt-14 drop:pb-10 drop:text-block-ink drop:sm:px-12 drop:sm:pt-20 drop:sm:pb-14",
        )}
      >
        {/* Drop: glossy sprites float behind the words. */}
        <div className="look-drop">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img
            src="/art/icons/sparklime.webp"
            alt=""
            aria-hidden
            className="pointer-events-none absolute top-5 right-5 -z-10 w-14 rotate-12 animate-float drop-shadow-xl sm:top-10 sm:right-[7%] sm:w-28"
          />
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img
            src="/art/icons/heartwhite.webp"
            alt=""
            aria-hidden
            className="pointer-events-none absolute right-[16%] bottom-10 -z-10 hidden w-24 -rotate-12 animate-float drop-shadow-xl [animation-delay:-3s] lg:block"
          />
        </div>

        <div className="min-w-0">
          <EchoSays>Creators, this one&apos;s for you.</EchoSays>
          {/* CSS rises, not JS reveals: the heading and lead paint before the page hydrates. */}
          <p
            className={cn(
              "animate-rise text-label text-brand-text",
              "renaissance:text-muted-foreground",
              "drop:font-sans drop:text-[17px] drop:leading-snug drop:font-semibold drop:tracking-[-0.02em] drop:text-block-ink drop:normal-case drop:sm:text-[19px]",
            )}
          >
            For creators
          </p>
          <h1
            id="apply-title"
            className={cn(
              "mt-4 max-w-4xl animate-rise text-h1 text-balance [animation-delay:60ms]",
              "drop:mt-3 drop:max-w-6xl drop:text-[clamp(2.75rem,1rem+5.4vw,6.5rem)] drop:leading-[0.9]",
            )}
          >
            Get paid to post about the AI and tech launches worth talking about.
          </h1>
          <p className="mt-5 max-w-[36rem] animate-rise text-lead text-pretty text-muted-foreground [animation-delay:120ms] drop:text-block-ink">
            We brief creators on new launches. You pick the campaigns you like, post on X and get paid.
          </p>
          {/* The rise sits on a wrapper: the links inside swap in once the address is read, and shouldn't rise twice. */}
          <div className="mt-8 animate-rise [animation-delay:180ms]">
            <ApplyCta surface="hero" />
          </div>
        </div>

        {/* Renaissance: Claude Lorrain's sunrise, hung beside the title. */}
        <div className="look-renaissance">
          <figure className="mt-2 min-w-0 animate-rise [animation-delay:240ms] lg:mt-0">
            <div className="relative aspect-[4/3] overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-8 ring-surface">
              <Image
                src="/art/sunrise-1860.webp"
                alt="Herders crossing a stream at first light, Claude Lorrain's Sunrise"
                fill
                sizes="(min-width: 1024px) 28rem, 100vw"
                className="object-cover transition-transform duration-[1.4s] ease-snap hover:scale-105"
              />
            </div>
            <figcaption className="mt-3 text-xs text-subtle-foreground">
              Claude Lorrain, Sunrise, about 1646 to 1647. The Met, public domain.
            </figcaption>
          </figure>
        </div>
      </div>
    </section>
  );
}

/**
 * Four steps from applying to getting paid. Renaissance draws a hairline over
 * each step, Agent has Echo tell it as a chat, Drop lines up color cards you
 * can swipe through on a phone.
 */
function HowItWorks() {
  return (
    <SectionShell id="how-it-works" label="How it works">
      <SectionTitle title="How it works." lead="From your application to your first payout, in four steps." />
      <EchoSays className="mt-10 mb-0">Here&apos;s the whole thing, start to finish.</EchoSays>
      <RevealGroup
        as="ol"
        className={cn(
          "mt-12 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4",
          "agent:mt-4 agent:flex agent:max-w-2xl agent:flex-col agent:gap-3 agent:pl-[3.75rem]",
          "drop:-mx-5 drop:flex drop:snap-x drop:snap-mandatory drop:gap-3 drop:overflow-x-auto drop:px-5 drop:pb-4 drop:[scrollbar-width:none] drop:lg:mx-0 drop:lg:grid drop:lg:overflow-visible drop:lg:px-0",
        )}
      >
        {STEPS.map((step, index) => (
          <RevealItem
            as="li"
            key={step.title}
            className={cn(
              "relative",
              "renaissance:pt-6",
              "agent:w-fit agent:max-w-full agent:rounded-[1.4rem] agent:bg-surface agent:px-5 agent:py-4 agent:shadow-soft agent:ring-1 agent:ring-border",
              index === 0 && "agent:rounded-tl-md",
              "drop:flex drop:min-h-[19rem] drop:w-[78%] drop:shrink-0 drop:snap-center drop:flex-col drop:justify-between drop:rounded-[1.75rem] drop:p-6 drop:text-block-ink drop:sm:w-[46%] drop:lg:w-auto",
              DROP_BLOCKS[index],
            )}
          >
            <span className="look-renaissance">
              <RuleDraw className="absolute inset-x-0 top-0 block h-px bg-foreground" />
            </span>
            <p className="text-[13px] font-semibold text-muted-foreground tabular-nums agent:hidden drop:font-[family-name:var(--font-anton)] drop:text-[64px] drop:leading-none drop:font-normal drop:text-block-ink/40">
              {String(index + 1).padStart(2, "0")}
            </p>
            <div>
              <h3 className="mt-3 text-[clamp(1.75rem,1.3rem+1.4vw,2.5rem)] leading-none font-bold tracking-[-0.045em] text-balance agent:mt-0 agent:text-[17px] agent:leading-snug agent:font-semibold agent:tracking-[-0.015em] drop:font-[family-name:var(--font-anton)] drop:text-[44px] drop:font-normal drop:tracking-[0.01em] drop:uppercase">
                {step.title}
                <span className="look-agent">.</span>
              </h3>
              <p className="mt-3 text-[15px] leading-relaxed text-pretty text-muted-foreground agent:mt-1 agent:text-foreground/80 drop:text-block-ink/90">
                {step.body}
              </p>
            </div>
          </RevealItem>
        ))}
      </RevealGroup>
    </SectionShell>
  );
}

/** Who we take on, and the shortcut for anyone holding an invite link. */
function WhatWeLookFor() {
  return (
    <SectionShell id="what-we-look-for" label="What we look for" className="pt-4 sm:pt-8">
      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)] lg:gap-20">
        <div>
          <EchoSays>I care who listens, not just how many.</EchoSays>
          <SectionTitle title="What we look for." lead="Follower count matters less than who listens." />
        </div>
        <div className="min-w-0">
          <RevealGroup
            as="ul"
            className={cn("grid gap-3", "renaissance:gap-0 renaissance:border-b renaissance:border-border-strong", "drop:gap-2.5")}
          >
            {LOOK_FOR.map(({ icon: Icon, title, body }) => (
              <RevealItem
                as="li"
                key={title}
                className={cn(
                  "flex items-start gap-4 rounded-[var(--radius-lg)] bg-surface p-5 shadow-soft ring-1 ring-border sm:p-6",
                  "renaissance:rounded-none renaissance:border-t renaissance:border-border-strong renaissance:bg-transparent renaissance:px-0 renaissance:py-6 renaissance:shadow-none renaissance:ring-0",
                  "drop:rounded-[1.5rem] drop:bg-surface-2 drop:shadow-none drop:ring-0",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-full bg-surface-2 text-brand-text",
                    "renaissance:bg-transparent renaissance:ring-1 renaissance:ring-border-strong",
                    "drop:bg-block-1 drop:text-block-ink",
                  )}
                >
                  <Icon className="size-[18px]" />
                </span>
                <div className="min-w-0">
                  <h3 className="text-[17px] leading-snug font-semibold tracking-[-0.02em] renaissance:text-[clamp(1.125rem,1rem+0.5vw,1.5rem)] renaissance:leading-tight renaissance:font-bold renaissance:tracking-[-0.035em]">
                    {title}
                  </h3>
                  <p className="mt-1 text-[15px] leading-relaxed text-pretty text-muted-foreground">{body}</p>
                </div>
              </RevealItem>
            ))}
          </RevealGroup>

          <Reveal
            className={cn(
              "mt-6 flex items-start gap-3.5 rounded-2xl border border-dashed border-border-strong px-4 py-4 sm:px-5",
              "renaissance:rounded-[var(--radius-sm)]",
            )}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-muted-foreground" aria-hidden>
              <Ticket className="size-4" />
            </span>
            <p className="min-w-0 text-[15px] leading-relaxed text-pretty">
              <span className="font-medium text-foreground">Got an invite link?</span>{" "}
              <span className="text-muted-foreground">Open it and you skip the queue.</span>
            </p>
          </Reveal>
        </div>
      </div>
    </SectionShell>
  );
}

/** The last word, on a color block, with the same way in. */
function ClosingCta() {
  return (
    <section
      aria-label="Apply now"
      className="px-3 pb-3 sm:px-5 sm:pb-5 renaissance:px-5 renaissance:sm:px-8 renaissance:lg:px-10"
    >
      <div
        className={cn(
          "relative isolate mx-auto flex max-w-[90rem] flex-col gap-8 overflow-hidden bg-block-1 px-6 py-12 text-block-ink sm:px-12 sm:py-16 lg:flex-row lg:items-end lg:justify-between",
          "renaissance:max-w-[84rem] renaissance:rounded-[var(--radius-sm)]",
          "agent:texture-noise agent:rounded-[2.5rem]",
          "drop:rounded-[2.25rem] drop:bg-block-5",
        )}
      >
        <div className="look-drop">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img
            src="/art/icons/bolt.webp"
            alt=""
            aria-hidden
            className="pointer-events-none absolute -top-2 right-4 -z-10 w-16 rotate-12 animate-float drop-shadow-xl sm:right-[10%] sm:w-28"
          />
        </div>
        <div className="max-w-3xl">
          <Reveal
            as="p"
            className="text-[15px] font-semibold renaissance:font-mono renaissance:text-[11px] renaissance:tracking-[0.08em] renaissance:uppercase"
          >
            Ready when you are
          </Reveal>
          <WordReveal
            as="h2"
            text="Apply in about five minutes."
            className={cn(
              "mt-3 text-[clamp(2rem,1.3rem+2.8vw,3.5rem)] leading-[0.98] font-bold tracking-[-0.045em] text-balance",
              "agent:font-medium agent:tracking-[-0.05em]",
              "drop:font-[family-name:var(--font-anton)] drop:text-[clamp(2.5rem,1.4rem+4.4vw,5.25rem)] drop:leading-[0.9] drop:font-normal drop:tracking-[0.005em] drop:uppercase",
            )}
          />
          <Reveal as="p" delay={0.12} className="mt-4 max-w-xl text-[16px] leading-relaxed text-pretty">
            We read every application ourselves and email you the answer. Once you&apos;re in, campaigns open to you
            show up in your dashboard.
          </Reveal>
        </div>
        <Reveal delay={0.18} className="shrink-0">
          <ApplyCta surface="block" />
        </Reveal>
      </div>
    </section>
  );
}
