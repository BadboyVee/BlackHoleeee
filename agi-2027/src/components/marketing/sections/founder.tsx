import Image from "next/image";

import { XLogo } from "@/components/brand/social-icons";
import { Reveal } from "@/components/motion/reveal";
import type { Founder } from "@/lib/founder";
import { cn } from "@/lib/utils";
import { EchoSays, SectionTitle } from "./shared";

const HEADING_ID = "founder-heading";

/** First and last initials, for the stand-in portrait when there's no photo. */
function initialsOf(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const picked = words.length > 1 ? [words[0], words[words.length - 1]] : words;
  return picked.map((word) => Array.from(word)[0]).join("").toUpperCase();
}

/** The X handle without its @, or null when there isn't one. */
function handleOf(xHandle: string | null) {
  const handle = xHandle?.trim().replace(/^@+/, "") ?? "";
  return handle || null;
}

/**
 * The portrait, framed in the look's voice: a hung canvas (Renaissance), a
 * soft rounded card (Agent), or a tilted sticker (Drop). With no photo it
 * shows the founder's initials on a color block instead.
 */
function Portrait({ founder }: { founder: Founder }) {
  const frame = cn(
    "relative aspect-[4/5] overflow-hidden",
    "renaissance:rounded-[var(--radius-sm)] renaissance:shadow-float renaissance:ring-[10px] renaissance:ring-surface",
    "agent:rounded-[2rem] agent:shadow-soft agent:ring-1 agent:ring-border",
    "drop:-rotate-2 drop:rounded-[1.75rem] drop:ring-4 drop:ring-white/25",
  );
  if (founder.photo) {
    return (
      <div className={frame}>
        <Image
          src={founder.photo.src}
          alt={founder.photo.alt}
          fill
          sizes="(min-width: 1024px) 26rem, (min-width: 640px) 18rem, 15rem"
          className="object-cover"
        />
      </div>
    );
  }
  // The name is the heading right beside it, so the initials are decoration.
  return (
    <div
      aria-hidden
      data-founder-initials
      className={cn(frame, "flex items-center justify-center bg-block-1 text-block-ink drop:bg-block-6 drop:text-white")}
    >
      <span className="text-[clamp(4.5rem,3rem+6vw,8.5rem)] leading-none font-bold tracking-[-0.06em] agent:font-medium drop:font-[family-name:var(--font-anton)] drop:font-normal drop:tracking-[0.01em]">
        {initialsOf(founder.name)}
      </span>
    </div>
  );
}

/**
 * Meet the founder: portrait beside a short bio, a pull quote and a link to
 * X. Renaissance sets it like a museum portrait, Agent has Echo introduce the
 * boss on a soft card, Drop puts it all on one juicy block. Renders nothing
 * until the founder's details are filled in (src/lib/founder.ts).
 */
function FounderSection({ founder }: { founder: Founder | null }) {
  if (!founder) return null;
  const handle = handleOf(founder.xHandle);
  const bio = founder.bio.filter((paragraph) => paragraph.trim());
  return (
    <section id="founder" aria-labelledby={HEADING_ID} className="relative scroll-mt-20 py-20 sm:py-28">
      <div className="mx-auto max-w-[84rem] px-5 sm:px-8 lg:px-10">
        <EchoSays>Meet my boss. I just work here.</EchoSays>
        <div
          className={cn(
            "grid gap-10 sm:gap-12 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:items-center lg:gap-16",
            "renaissance:border-t renaissance:border-border-strong renaissance:pt-10 renaissance:sm:pt-14",
            "agent:rounded-[2.5rem] agent:bg-surface agent:p-6 agent:shadow-soft agent:ring-1 agent:ring-border agent:sm:p-10 agent:lg:p-12",
            "drop:rounded-[2.25rem] drop:bg-block-4 drop:p-6 drop:text-white drop:sm:p-10 drop:lg:p-14",
          )}
        >
          <Reveal className="relative w-full max-w-[15rem] sm:max-w-[18rem] lg:max-w-none">
            <Portrait founder={founder} />
            <span className="look-drop">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
              <img
                src="/art/icons/sparklime.webp"
                alt=""
                aria-hidden
                loading="lazy"
                className="pointer-events-none absolute -top-5 -right-5 z-10 w-16 animate-float drop-shadow-xl sm:w-20"
              />
            </span>
          </Reveal>

          <div className="min-w-0">
            <Reveal
              as="p"
              className="text-label text-muted-foreground agent:text-brand-text drop:font-sans drop:text-[17px] drop:font-semibold drop:tracking-[-0.02em] drop:normal-case drop:text-white"
            >
              Meet the founder
            </Reveal>
            <div id={HEADING_ID} className="mt-3">
              <SectionTitle title={founder.name} />
            </div>
            <Reveal
              as="p"
              delay={0.08}
              className="mt-3 text-lead break-words text-muted-foreground agent:text-foreground/80 drop:font-semibold drop:text-white/90"
            >
              {founder.role}
            </Reveal>

            {bio.length > 0 ? (
              <div className="mt-6 flex max-w-[38rem] flex-col gap-4">
                {bio.map((paragraph, index) => (
                  <Reveal
                    as="p"
                    key={index}
                    delay={0.12 + index * 0.05}
                    className="text-[16px] leading-relaxed text-pretty break-words text-muted-foreground agent:text-foreground/80 drop:text-white/90"
                  >
                    {paragraph}
                  </Reveal>
                ))}
              </div>
            ) : null}

            {founder.quote ? (
              <Reveal delay={0.2} className="mt-8">
                <blockquote
                  className={cn(
                    // Renaissance: an editorial pull quote on a hairline.
                    "max-w-[34rem] border-l-2 border-border-strong pl-5 text-[clamp(1.25rem,1.05rem+0.8vw,1.75rem)] leading-snug font-bold tracking-[-0.035em] text-balance break-words",
                    // Agent: a chat bubble, like Echo's.
                    "agent:w-fit agent:rounded-[1.4rem] agent:rounded-bl-md agent:border-0 agent:bg-block-3 agent:px-5 agent:py-4 agent:text-[17px] agent:font-medium agent:tracking-[-0.015em] agent:text-foreground",
                    // Drop: giant condensed capitals, right on the block.
                    "drop:border-0 drop:pl-0 drop:font-[family-name:var(--font-anton)] drop:text-[clamp(1.75rem,1.3rem+1.8vw,3rem)] drop:leading-[0.95] drop:font-normal drop:tracking-[0.01em] drop:uppercase",
                  )}
                >
                  <p>&ldquo;{founder.quote}&rdquo;</p>
                </blockquote>
              </Reveal>
            ) : null}

            {handle ? (
              <Reveal delay={0.25} className="mt-8">
                <a
                  href={`https://x.com/${encodeURIComponent(handle)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pressable inline-flex h-12 max-w-full items-center justify-center gap-2 rounded-full bg-foreground px-6 text-[15px] font-semibold text-background transition-transform duration-200 ease-snap hover:-translate-y-0.5 agent:font-medium drop:bg-white drop:text-block-4"
                >
                  <XLogo className="size-4 shrink-0" />
                  <span className="truncate">{`Follow @${handle} on X`}</span>
                  <span className="sr-only"> (opens in a new tab)</span>
                </a>
              </Reveal>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

export { FounderSection };
