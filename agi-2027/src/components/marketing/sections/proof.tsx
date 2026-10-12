import Image from "next/image";
import { ArrowUpRight, Eye, Heart, MessageCircle, Repeat2 } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { Reveal, RevealGroup, RevealItem } from "@/components/motion/reveal";
import { byViews, mediaAspect, showcasePosts, STATS_AS_OF, type ShowcasePost } from "@/lib/showcase-posts";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";
import { PostAvatar, PostText, VerifiedBadge } from "../x-post";
import { EchoSays, SectionShell, SectionTitle } from "./shared";

/** Drop cards each take a juicy color and a little tilt. */
const DROP_CARD = ["drop:bg-block-1", "drop:bg-block-5", "drop:bg-block-2"];
const DROP_TILT = ["drop:-rotate-2", "drop:rotate-1", "drop:-rotate-1"];

/** The numbers a card can show, in order of preference; up to three that X showed. */
const METRICS = [
  ["views", "Views", Eye],
  ["likes", "Likes", Heart],
  ["reposts", "Reposts", Repeat2],
  ["replies", "Replies", MessageCircle],
] as const;

function PostCard({ post, index }: { post: ShowcasePost; index: number }) {
  const { author, media, stats } = post;
  const metrics = METRICS.filter(([key]) => stats[key]).slice(0, 3);
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
        <PostAvatar
          author={author}
          className="size-10 ring-2 ring-white/40 transition-transform duration-300 ease-spring-snappy group-hover:scale-110"
        />
        <span className="min-w-0">
          <span className="flex items-center gap-1 text-[15px] font-semibold tracking-[-0.015em]">
            <span className="truncate">{author.name}</span>
            <VerifiedBadge badge={author.badge} className="size-4 shrink-0" />
          </span>
          <span className="block truncate text-sm text-subtle-foreground drop:text-white/75">@{author.handle}</span>
        </span>
        <a
          href={post.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Open ${author.name}’s post on X`}
          className="pressable -m-2 ml-auto flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground drop:text-white/80 drop:hover:text-white"
        >
          <XLogo className="size-4" />
        </a>
      </header>
      <PostText
        post={post}
        max={280}
        className="mt-4 flex-1 text-[15px] leading-relaxed text-pretty"
        accentClassName="text-[#1d9bf0] drop:font-semibold drop:text-white drop:underline drop:underline-offset-2"
        more={
          <>
            {" "}
            <a
              href={post.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold whitespace-nowrap text-brand-text underline-offset-4 hover:underline drop:text-white drop:underline"
            >
              Show more on X
            </a>
          </>
        }
      />
      <figure className="mt-4">
        <div
          className="relative overflow-hidden rounded-[var(--radius-lg)] bg-surface-2 ring-1 ring-border drop:ring-white/20"
          style={{ aspectRatio: mediaAspect(media) }}
        >
          <Image
            src={media.src}
            alt={media.alt}
            fill
            sizes="(min-width: 1024px) 380px, (min-width: 640px) 45vw, 84vw"
            className="object-cover"
            style={{ objectPosition: media.focus }}
          />
        </div>
        {media.kind === "link" && media.from ? (
          <figcaption className="mt-1.5 text-xs text-subtle-foreground drop:text-white/75">From {media.from}</figcaption>
        ) : null}
      </figure>
      <p className="mt-4 text-xs text-subtle-foreground drop:text-white/80">
        Posted on X, {formatUtcDate(post.postedAt)}
      </p>
      {metrics.length > 0 ? (
        <footer className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 drop:border-white/25">
          {metrics.map(([key, label, Icon]) => (
            <span key={key} className="flex flex-col">
              <span className="text-[22px] leading-none font-bold tracking-[-0.04em] tabular-nums agent:text-brand-text drop:font-[family-name:var(--font-anton)] drop:text-[26px] drop:font-normal drop:tracking-[0.01em] drop:text-white">
                {stats[key]}
              </span>
              <span className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground drop:text-white/80">
                <Icon className="size-3" aria-hidden />
                {label}
              </span>
            </span>
          ))}
        </footer>
      ) : (
        <footer className="mt-4 border-t border-border pt-4 drop:border-white/25">
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold underline-offset-4 hover:underline"
          >
            See the numbers on X
            <ArrowUpRight className="size-4" aria-hidden />
          </a>
        </footer>
      )}
    </article>
  );
}

/** Real launch posts on X, most viewed first, each with the numbers X showed. */
function ProofSection() {
  const posts = byViews(showcasePosts);
  return (
    <SectionShell id="proof" label="Proof">
      <EchoSays>These are real launch posts. Open any of them on X.</EchoSays>
      <SectionTitle
        title="Posts that moved launches."
        lead="Real launch posts from AI companies, with the numbers X showed for each."
      />
      <div className="mt-12 grid gap-8 renaissance:lg:grid-cols-[minmax(0,0.8fr)_minmax(0,2fr)] renaissance:lg:items-start">
        {/* Renaissance: a framed detail of the hero painting, hung beside the posts. */}
        <div className="look-renaissance">
          <Reveal className="hidden lg:sticky lg:top-24 lg:block">
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
        <div className="min-w-0">
          <RevealGroup className="-mx-5 flex snap-x snap-mandatory gap-4 overflow-x-auto px-5 pt-2 pb-4 [scrollbar-width:none] sm:mx-0 sm:block sm:columns-2 sm:gap-6 sm:overflow-visible sm:px-0 lg:columns-3 renaissance:lg:columns-2">
            {posts.map((post, index) => (
              <RevealItem key={post.id} className="w-[84%] shrink-0 snap-center sm:mb-6 sm:w-auto sm:break-inside-avoid">
                <PostCard post={post} index={index} />
              </RevealItem>
            ))}
          </RevealGroup>
          <p className="mt-2 text-xs text-subtle-foreground">
            Numbers as X showed them on {formatUtcDate(STATS_AS_OF)}.
          </p>
        </div>
      </div>
    </SectionShell>
  );
}

export { ProofSection };
