import Image from "next/image";
import { ArrowUpRight } from "lucide-react";

import { Fragment } from "react";

import { Reveal } from "@/components/motion/reveal";
import { combinedFollowers, type RosterCreator } from "@/lib/creator-roster";
import { bareXHandle, formatXCount, xProfileUrl } from "@/lib/creators/display";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";
import { RosterGrid, RosterItem } from "./roster-grid";
import { EchoSays, SectionTitle } from "./shared";

const HEADING_ID = "roster-heading";

/**
 * Drop cards are stickers: each takes a juicy color and a little tilt. Five
 * colors and four tilts, so on a grid of three, four or seven across the colors
 * fall diagonally instead of lining up in columns.
 */
const DROP_CARD = ["drop:bg-block-1", "drop:bg-block-4", "drop:bg-block-3", "drop:bg-block-6", "drop:bg-block-5"];
const DROP_TILT = ["drop:-rotate-2", "drop:rotate-1", "drop:-rotate-1", "drop:rotate-2"];

/**
 * A name that may wrap on a narrow card, and then between its words or where
 * its capitals join them ("Mystique" and "Mide"), never cut off.
 */
function Wrappable({ text }: { text: string }) {
  return text.split(/(?<=[a-z])(?=[A-Z])/).map((part, index) => (
    <Fragment key={index}>
      {index > 0 ? <wbr /> : null}
      {part}
    </Fragment>
  ));
}

/**
 * One creator: picture, name, handle and followers, and the whole card links
 * to their X profile. Renaissance hangs a matted portrait over a wall label,
 * Agent sets it on a soft card, Drop makes it a tilted color sticker. Small
 * text on the Drop colors stays full white, so it's easy to read.
 */
function CreatorCard({ creator, index }: { creator: RosterCreator; index: number }) {
  const handle = bareXHandle(creator.xHandle);
  const count = formatXCount(creator.followers);
  const unit = creator.followers === 1 ? "follower" : "followers";
  return (
    <a
      href={xProfileUrl(handle)}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group relative flex h-full min-w-0 flex-col items-center px-1 pt-4 pb-3 text-center sm:px-3 sm:pt-6 sm:pb-5 md:px-4",
        // Tailwind moves and tilts with the translate and rotate properties, not transform.
        "transition-[translate,rotate,box-shadow,background-color] duration-300 ease-snap motion-safe:hover:-translate-y-1",
        // Renaissance: a matted portrait over a museum wall label.
        "renaissance:rounded-[var(--radius-sm)] renaissance:bg-surface renaissance:ring-1 renaissance:ring-border renaissance:hover:shadow-float renaissance:hover:ring-border-strong",
        // Agent: a soft rounded card.
        "agent:rounded-[1.5rem] agent:bg-surface agent:shadow-soft agent:ring-1 agent:ring-border agent:hover:shadow-float agent:sm:rounded-[1.75rem]",
        // Drop: a tilted color sticker that straightens up on hover.
        "drop:rounded-[1.25rem] drop:text-white drop:shadow-soft drop:hover:rotate-0 drop:hover:shadow-float drop:sm:rounded-[1.5rem]",
        DROP_CARD[index % DROP_CARD.length],
        DROP_TILT[index % DROP_TILT.length],
      )}
    >
      <span
        className={cn(
          "relative block size-15 shrink-0 overflow-hidden rounded-full bg-surface-2 sm:size-18 lg:size-22 xl:size-24",
          "transition-transform duration-300 ease-spring-snappy motion-safe:group-hover:scale-105",
          // A round canvas in a mat with a hairline frame, hung with a soft shadow.
          "renaissance:shadow-soft renaissance:ring-1 renaissance:ring-border-strong renaissance:ring-offset-4 renaissance:ring-offset-surface renaissance:sm:ring-offset-[6px]",
          "agent:ring-1 agent:ring-border",
          "drop:ring-[3px] drop:ring-white/35",
        )}
      >
        <Image
          src={creator.avatar}
          alt=""
          fill
          sizes="(min-width: 1280px) 96px, (min-width: 1024px) 88px, (min-width: 640px) 72px, 60px"
          className="object-cover"
        />
      </span>
      {/* The visible text is hidden from screen readers, which hear the one sentence below instead. */}
      <span
        aria-hidden
        className="mt-3 block w-full text-[13px] leading-tight font-semibold tracking-[-0.015em] [overflow-wrap:anywhere] sm:mt-4 sm:text-[15px] agent:font-medium drop:font-bold"
      >
        <Wrappable text={creator.name} />
      </span>
      <span
        aria-hidden
        className="mt-0.5 block w-full truncate text-[11px] leading-tight tracking-[-0.01em] text-subtle-foreground sm:text-[12px] sm:tracking-normal md:text-[13px] drop:text-white"
      >
        @{handle}
      </span>
      <span
        aria-hidden
        className={cn(
          "mt-auto flex w-full flex-col items-center pt-3 sm:pt-4",
          "renaissance:mt-3 renaissance:border-t renaissance:border-border renaissance:sm:mt-4",
        )}
      >
        <span className="text-[16px] leading-none font-bold tracking-[-0.035em] tabular-nums sm:text-[19px] agent:font-medium agent:text-brand-text drop:font-[family-name:var(--font-anton)] drop:text-[22px] drop:font-normal drop:tracking-[0.01em] drop:sm:text-[28px]">
          {count}
        </span>
        <span className="mt-1 text-label leading-none text-subtle-foreground agent:font-sans agent:text-[12px] agent:tracking-normal agent:normal-case drop:font-sans drop:text-[12px] drop:font-semibold drop:tracking-normal drop:text-white drop:normal-case">
          {unit}
        </span>
      </span>
      <span className="sr-only">{`${creator.name}, @${handle} on X, ${count} ${unit}`}</span>
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

/**
 * The creators behind the launches: rows of profile cards, three across on a
 * phone (two on the narrowest) and up to seven on a wide screen (two even rows
 * for the owner's 14), each linking to the creator on X. A last row that isn't
 * full is centered.
 * Under it, a line for creators who work with us and aren't listed yet, which
 * links to `contactXHandle` on X (the founder's, from src/lib/founder.ts) and
 * is left out when there's no handle.
 * Renders nothing until the owner adds creators (src/lib/creator-roster.ts).
 */
function CreatorRosterSection({
  creators,
  asOf,
  contactXHandle = null,
}: {
  creators: RosterCreator[];
  asOf: string | null;
  contactXHandle?: string | null;
}) {
  if (creators.length === 0) return null;
  const total = combinedFollowers(creators);
  const contact = bareXHandle(contactXHandle ?? "") || null;
  return (
    <section id="roster" aria-labelledby={HEADING_ID} className="relative scroll-mt-20 py-20 sm:py-28">
      <div className="mx-auto max-w-[84rem] px-5 sm:px-8 lg:px-10">
        <EchoSays>Meet the people I brief.</EchoSays>
        <div
          className={cn(
            "relative grid gap-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end lg:gap-16",
            "renaissance:border-t renaissance:border-border-strong renaissance:pt-10 renaissance:sm:pt-14",
          )}
        >
          <div className="min-w-0">
            <Reveal
              as="p"
              className="text-label text-muted-foreground agent:text-brand-text drop:font-sans drop:text-[17px] drop:font-semibold drop:tracking-[-0.02em] drop:normal-case"
            >
              The roster
            </Reveal>
            <div className="mt-3">
              <SectionTitle
                titleId={HEADING_ID}
                title="The creators behind the launches."
                lead="Real people with real followings on X. Open any profile to see for yourself."
              />
            </div>
          </div>
          <Reveal delay={0.15} className="relative">
            <p className="flex items-baseline gap-3 lg:flex-col lg:items-end lg:gap-1 lg:text-right">
              <span className="text-[clamp(2.25rem,1.6rem+2.4vw,3.75rem)] leading-[0.9] font-bold tracking-[-0.055em] tabular-nums agent:font-medium agent:text-brand-text drop:font-[family-name:var(--font-anton)] drop:text-[clamp(2.75rem,2rem+3vw,4.75rem)] drop:font-normal drop:tracking-[0.01em]">
                {formatXCount(total)}
              </span>{" "}
              <span className="text-[15px] leading-snug text-muted-foreground">
                {creators.length === 1 ? "followers on X" : "followers between them"}
              </span>
            </p>
            <span className="look-drop">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img
                src="/art/icons/bubble.webp"
                alt=""
                aria-hidden
                loading="lazy"
                className="pointer-events-none absolute -top-24 right-2 hidden w-20 animate-float drop-shadow-xl lg:block"
              />
            </span>
          </Reveal>
        </div>

        {/* Rows of --cols cards (--gap apart) that wrap and center, so a short last row sits in the middle. */}
        <RosterGrid className="mt-10 flex flex-wrap justify-center gap-(--gap) [--cols:2] [--gap:0.625rem] min-[360px]:[--cols:3] sm:mt-14 sm:[--cols:4] sm:[--gap:1rem] lg:[--cols:5] xl:[--cols:7] drop:sm:[--gap:1.25rem]">
          {creators.map((creator, index) => (
            <RosterItem
              key={creator.xHandle}
              index={index}
              className="w-[calc((100%_-_(var(--cols)_-_1)_*_var(--gap))_/_var(--cols))] min-w-0"
            >
              <CreatorCard creator={creator} index={index} />
            </RosterItem>
          ))}
        </RosterGrid>

        {asOf || contact ? (
          <div className="mt-6 flex flex-col gap-2 sm:mt-8 sm:flex-row-reverse sm:items-center sm:justify-between sm:gap-6">
            {contact ? (
              <p className="text-[15px] leading-snug text-muted-foreground">
                One of our creators and not on here?{" "}
                <a
                  href={xProfileUrl(contact)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "inline-flex min-h-11 items-center gap-1 font-semibold whitespace-nowrap text-foreground underline decoration-border-strong underline-offset-4 transition-colors hover:decoration-current",
                    "agent:text-brand-text drop:font-bold",
                  )}
                >
                  Message us on X
                  <ArrowUpRight aria-hidden className="size-4 shrink-0" />
                  <span className="sr-only"> (opens in a new tab)</span>
                </a>
              </p>
            ) : null}
            {asOf ? (
              <p className="text-xs text-subtle-foreground">Follower counts as X showed them on {formatUtcDate(asOf)}.</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export { CreatorRosterSection };
