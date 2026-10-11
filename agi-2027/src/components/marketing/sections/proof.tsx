import Image from "next/image";
import { Eye, Heart, Repeat2 } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { Reveal, RevealGroup, RevealItem } from "@/components/motion/reveal";
import { featuredPosts, type FeaturedPost } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";
import { EchoSays, SectionShell, SectionTitle } from "./shared";

const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

/** Drop cards each take a juicy color and a little tilt. */
const DROP_CARD = ["drop:bg-block-1", "drop:bg-block-5", "drop:bg-block-2"];
const DROP_TILT = ["drop:-rotate-2", "drop:rotate-1", "drop:-rotate-1"];

function PostCard({ post, index }: { post: FeaturedPost; index: number }) {
  const { creator, metrics } = post;
  return (
    <article
      className={cn(
        "group relative flex h-full flex-col rounded-[var(--radius-xl)] bg-surface p-6 shadow-soft ring-1 ring-border transition-[transform,box-shadow] duration-300 ease-snap hover:-translate-y-1 hover:shadow-float",
        "drop:text-white drop:ring-0 drop:hover:rotate-0",
        DROP_CARD[index % 3],
        DROP_TILT[index % 3],
      )}
    >
      <header className="flex items-center gap-3">
        <span
          aria-hidden
          className="flex size-10 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold text-white ring-2 ring-white/40 transition-transform duration-300 ease-spring-snappy group-hover:scale-110"
          style={{
            background: `linear-gradient(140deg, hsl(${creator.hue} 70% 62%), hsl(${creator.hue + 40} 60% 38%))`,
          }}
        >
          {creator.initials}
        </span>
        <span className="min-w-0">
          <span className="block truncate text-[15px] font-semibold tracking-[-0.015em]">{creator.name}</span>
          <span className="block truncate text-sm text-subtle-foreground drop:text-white/75">@{creator.handle}</span>
        </span>
        <XLogo className="ml-auto size-4 shrink-0 text-muted-foreground drop:text-white/80" />
      </header>
      <p className="mt-4 flex-1 text-[15.5px] leading-relaxed text-pretty">{post.text}</p>
      <p className="mt-4 text-xs text-subtle-foreground drop:text-white/80">
        Paid partnership. {post.brand}, {post.moment.toLowerCase()}.
      </p>
      <footer className="mt-5 grid grid-cols-3 gap-2 border-t border-border pt-4 drop:border-white/25">
        {(
          [
            ["Views", metrics.views, Eye],
            ["Likes", metrics.likes, Heart],
            ["Reposts", metrics.reposts, Repeat2],
          ] as const
        ).map(([label, value, Icon]) => (
          <span key={label} className="flex flex-col">
            <span className="text-[22px] leading-none font-bold tracking-[-0.04em] tabular-nums agent:text-brand-text drop:font-[family-name:var(--font-anton)] drop:text-[26px] drop:font-normal drop:tracking-[0.01em] drop:text-white">
              {compact.format(value)}
            </span>
            <span className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground drop:text-white/80">
              <Icon className="size-3" aria-hidden />
              {label}
            </span>
          </span>
        ))}
      </footer>
    </article>
  );
}

/** Featured posts from past campaigns, each with its numbers. */
function ProofSection() {
  return (
    <SectionShell id="proof" label="Proof">
      <EchoSays>Here&apos;s what creators posted for launches like yours.</EchoSays>
      <SectionTitle
        title="Posts that moved launches."
        lead="Every campaign ends with the numbers: views, likes, reposts and replies, post by post."
      />
      <div className="mt-12 grid gap-8 renaissance:lg:grid-cols-[minmax(0,0.8fr)_minmax(0,2fr)] renaissance:lg:items-center">
        {/* Renaissance: a framed detail of the hero painting, hung beside the posts. */}
        <div className="look-renaissance">
          <Reveal className="hidden lg:block">
            <figure>
              <div className="relative aspect-[3/4] overflow-hidden rounded-[var(--radius-sm)] shadow-float ring-8 ring-surface">
                <Image
                  src="/art/detail-hand.webp"
                  alt="Detail of Orion's reaching hand from Poussin's painting"
                  fill
                  sizes="(min-width: 1024px) 25vw, 0px"
                  className="object-cover object-[40%_50%] transition-transform duration-[1.2s] ease-snap hover:scale-105"
                />
              </div>
              <figcaption className="mt-3 text-xs text-subtle-foreground">
                Detail, Nicolas Poussin, Blind Orion Searching for the Rising Sun, 1658.
              </figcaption>
            </figure>
          </Reveal>
        </div>
        <RevealGroup className="-mx-5 flex snap-x snap-mandatory gap-4 overflow-x-auto px-5 pt-2 pb-4 [scrollbar-width:none] sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-3">
          {featuredPosts.map((post, index) => (
            <RevealItem key={post.creator.handle} className="w-[84%] shrink-0 snap-center sm:w-auto">
              <PostCard post={post} index={index} />
            </RevealItem>
          ))}
        </RevealGroup>
      </div>
    </SectionShell>
  );
}

export { ProofSection };
