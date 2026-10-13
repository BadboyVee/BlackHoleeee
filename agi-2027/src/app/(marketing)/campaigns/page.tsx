import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Megaphone } from "lucide-react";

import { PublicCampaignCard } from "@/components/campaign/public-campaign-card";
import { MarketingMain } from "@/components/layout/marketing-main";
import { EchoSays } from "@/components/marketing/sections/shared";
import { Reveal, RevealGroup, RevealItem, WordReveal } from "@/components/motion/reveal";
import { StatusDot } from "@/components/status-badge";
import { DEMO_BOARD_NOW, publicCampaigns } from "@/lib/campaigns/public";
import { cn } from "@/lib/utils";

const LEAD = "Live campaigns from AI and tech startups. Sign up to see the payout and claim a slot.";

export const metadata: Metadata = {
  title: "Open campaigns",
  description: LEAD,
  alternates: { canonical: "/campaigns" },
};

/**
 * The public campaign board. Anyone can browse what's live; the payout and
 * the Claim button sit behind sign up.
 *
 * The board is filtered at a fixed demo moment (DEMO_BOARD_NOW), not the real
 * clock. The demo data is a snapshot, so the real clock would empty it, and a
 * fixed time keeps this page fully prerendered: there is no request-time read
 * to wrap in Suspense. Post windows still show in each viewer's own time zone
 * because LocalTimeRange swaps them in after hydration. Milestone 5 reads the
 * board from the database instead, where the database's own clock does the
 * filtering, and this page stays the same.
 */
export default function OpenCampaignsPage() {
  const campaigns = publicCampaigns(new Date(DEMO_BOARD_NOW));
  const full = campaigns.filter((campaign) => campaign.status === "full").length;
  const open = campaigns.length - full;
  const summary = campaigns.length === 0 ? "Nothing open right now" : full > 0 ? `${open} open, ${full} full` : `${open} open now`;

  return (
    <MarketingMain>
      <BoardHeader summary={summary} live={open > 0} />

      <section aria-label="Campaigns" className="mx-auto max-w-[84rem] px-5 pt-8 sm:px-8 sm:pt-10 lg:px-10">
        {campaigns.length > 0 ? (
          <>
            <RevealGroup as="ul" className="grid gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3 renaissance:gap-6">
              {campaigns.map((campaign, index) => (
                <RevealItem as="li" key={campaign.id} className="min-w-0">
                  <PublicCampaignCard campaign={campaign} index={index} />
                </RevealItem>
              ))}
            </RevealGroup>
            <p className="mt-5 text-xs text-subtle-foreground">
              Post windows show in your time zone, with UTC below. Demo campaigns until the agency&apos;s board goes live.
            </p>
          </>
        ) : (
          <EmptyBoard />
        )}
      </section>

      <CreatorsPitch />
    </MarketingMain>
  );
}

/** Title, lead and a live count, in each look's voice. */
function BoardHeader({ summary, live }: { summary: string; live: boolean }) {
  return (
    <section aria-label="Open campaigns" className="px-0 drop:px-3 drop:pt-3 drop:sm:px-5 drop:sm:pt-5">
      <div
        className={cn(
          "relative isolate mx-auto max-w-[84rem] px-5 pt-12 sm:px-8 sm:pt-16 lg:px-10",
          "renaissance:grid renaissance:items-end renaissance:gap-10 renaissance:lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]",
          "drop:max-w-[90rem] drop:overflow-hidden drop:rounded-[2.25rem] drop:bg-block-1 drop:px-6 drop:pt-14 drop:pb-10 drop:text-white drop:sm:px-12 drop:sm:pt-20 drop:sm:pb-14",
        )}
      >
        {/* Drop: glossy sprites float around the giant word. */}
        <div className="look-drop">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img
            src="/art/icons/bolt.webp"
            alt=""
            aria-hidden
            className="pointer-events-none absolute top-5 right-5 -z-10 w-14 rotate-12 animate-float drop-shadow-xl sm:top-10 sm:right-[7%] sm:w-28"
          />
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img
            src="/art/icons/heartwhite.webp"
            alt=""
            aria-hidden
            className="pointer-events-none absolute right-[22%] bottom-8 -z-10 hidden w-24 -rotate-12 animate-float drop-shadow-xl [animation-delay:-3s] lg:block"
          />
        </div>

        <div className="min-w-0">
          <EchoSays>Here&apos;s what&apos;s live right now. Payouts unlock when you sign up.</EchoSays>
          <div className="look-renaissance">
            <Reveal as="p" className="mb-4 font-mono text-[11px] tracking-[0.08em] text-muted-foreground uppercase">
              The board <span aria-hidden>/</span> Creator Edition
            </Reveal>
          </div>
          <div className="look-drop">
            <Reveal as="p" className="text-[17px] font-semibold tracking-[-0.02em] sm:text-[19px]">
              Fresh drops for creators
            </Reveal>
          </div>

          <WordReveal
            as="h1"
            text="Open campaigns"
            className={cn(
              "text-h1 text-balance",
              "drop:mt-2 drop:text-[clamp(3.75rem,1.2rem+10.5vw,10.5rem)] drop:leading-[0.86]",
            )}
          />
          <Reveal
            as="p"
            delay={0.12}
            className="mt-5 max-w-[36rem] text-lead text-pretty text-muted-foreground drop:text-white"
          >
            {LEAD}
          </Reveal>
          <Reveal delay={0.2} className="mt-6 flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "inline-flex h-9 items-center gap-2 rounded-full bg-surface px-3.5 text-sm font-semibold shadow-soft ring-1 ring-border",
                "renaissance:rounded-[var(--radius-sm)] renaissance:bg-transparent renaissance:font-mono renaissance:text-[12px] renaissance:tracking-[0.06em] renaissance:uppercase renaissance:shadow-none",
                "drop:bg-white drop:text-block-1 drop:shadow-none drop:ring-0",
              )}
            >
              {live ? <StatusDot tone="brand" pulse className="drop:text-block-1" /> : null}
              {summary}
            </span>
          </Reveal>
        </div>

        {/* Renaissance: a storm breaking, hung beside the title. */}
        <div className="look-renaissance">
          <Reveal className="hidden lg:block">
            <figure>
              <div className="relative aspect-[5/4] overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-8 ring-surface">
                <Image
                  src="/art/detail-storm.webp"
                  alt="A storm breaking over a valley, a detail from Thomas Cole's The Oxbow"
                  fill
                  sizes="(min-width: 1024px) 24rem, 0px"
                  className="object-cover transition-transform duration-[1.4s] ease-snap hover:scale-105"
                />
              </div>
              <figcaption className="mt-3 text-xs text-subtle-foreground">
                Detail, Thomas Cole, The Oxbow, 1836. The Met, public domain.
              </figcaption>
            </figure>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function EmptyBoard() {
  return (
    <Reveal
      className={cn(
        "flex flex-col items-center rounded-[var(--radius-xl)] border bg-surface/60 px-6 py-16 text-center sm:py-20",
        "renaissance:rounded-[var(--radius-sm)] renaissance:border-border-strong",
      )}
    >
      <span className="mb-5 flex size-12 items-center justify-center rounded-full bg-surface-2 ring-1 ring-border">
        <Megaphone className="size-5 text-muted-foreground" aria-hidden />
      </span>
      <h2 className="text-h3">No open campaigns right now</h2>
      <p className="mt-2 max-w-sm text-[15px] text-pretty text-muted-foreground">
        New ones drop most weeks. Apply now so you&apos;re ready to claim the next one.
      </p>
      <Link
        href="/apply"
        className="pressable mt-6 inline-flex h-11 items-center gap-2 rounded-full bg-foreground px-5 text-[15px] font-semibold text-background agent:bg-brand agent:text-brand-foreground renaissance:rounded-[var(--radius-sm)]"
      >
        Apply as a creator
        <ArrowRight className="size-4" aria-hidden />
      </Link>
    </Reveal>
  );
}

/** The nudge for creators who aren't in yet. */
function CreatorsPitch() {
  return (
    <section aria-label="For creators" className="px-3 pt-16 pb-3 sm:px-5 sm:pt-24 sm:pb-5 renaissance:px-5 renaissance:sm:px-8 renaissance:lg:px-10">
      <div
        className={cn(
          "relative isolate mx-auto flex max-w-[90rem] flex-col gap-8 overflow-hidden px-6 py-12 text-block-ink sm:px-12 sm:py-16 lg:flex-row lg:items-end lg:justify-between",
          "bg-block-1",
          "renaissance:max-w-[84rem] renaissance:rounded-[var(--radius-sm)]",
          "agent:texture-noise agent:rounded-[2.5rem]",
          "drop:rounded-[2.25rem] drop:bg-block-5",
        )}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
        <img
          src="/art/icons/sparklime.webp"
          alt=""
          aria-hidden
          className="pointer-events-none absolute -top-2 right-4 -z-10 hidden w-20 animate-float drop-shadow-xl drop:block sm:right-[10%] sm:w-28"
        />
        <div className="max-w-3xl">
          <Reveal as="p" className="text-[15px] font-semibold renaissance:font-mono renaissance:text-[11px] renaissance:tracking-[0.08em] renaissance:uppercase">
            For creators
          </Reveal>
          <WordReveal
            as="h2"
            text="Get paid to post about launches you'd talk about anyway."
            className={cn(
              "mt-3 text-[clamp(2rem,1.3rem+2.8vw,3.5rem)] leading-[0.98] font-bold tracking-[-0.045em] text-balance",
              "agent:font-medium agent:tracking-[-0.05em]",
              "drop:font-[family-name:var(--font-anton)] drop:text-[clamp(2.5rem,1.4rem+4.4vw,5.25rem)] drop:leading-[0.9] drop:font-normal drop:tracking-[0.005em] drop:uppercase",
            )}
          />
          <Reveal as="p" delay={0.12} className="mt-4 max-w-xl text-[16px] leading-relaxed">
            Apply once. When you&apos;re in, you see every payout, claim a slot in one tap and get paid per post.
          </Reveal>
        </div>
        <Reveal delay={0.18} className="shrink-0">
          <Link
            href="/apply"
            className={cn(
              "pressable group inline-flex h-12 items-center gap-2 rounded-full bg-white px-6 text-[15px] font-semibold text-[#16120f] transition-transform duration-200 ease-snap hover:-translate-y-0.5",
              "renaissance:rounded-[var(--radius-sm)] renaissance:bg-brand renaissance:text-brand-foreground",
            )}
          >
            Apply as a creator
            <ArrowRight className="size-4 transition-transform duration-200 ease-snap group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
