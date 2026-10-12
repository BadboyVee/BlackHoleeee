"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AnimatePresence,
  motion,
  useMotionValue,
  useReducedMotion,
  useSpring,
  useTransform,
  type MotionValue,
} from "motion/react";
import { ArrowLeft, ArrowRight, ArrowUpRight, Bookmark, Heart, MessageCircle, Repeat2, Share2 } from "lucide-react";

import { useLook } from "@/components/theme/look-picker";
import { getShowcasePost, mediaAspect, STATS_AS_OF, type ShowcasePost } from "@/lib/showcase-posts";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";
import { PostAvatar, PostText, VerifiedBadge } from "../x-post";
import { dropSlides, type DropIcon, type DropSlide } from "./drop-slides";

const AUTO_MS = 6500;
const snappy = { type: "spring", stiffness: 400, damping: 30 } as const;
const smooth = { type: "spring", stiffness: 200, damping: 24 } as const;

/** Fit a word across the screen: Anton's capitals average about 0.53em wide. */
function wordSize(word: string) {
  return `min(${(90 / (word.length * 0.53)).toFixed(2)}vw, 50svh)`;
}

/**
 * Drop hero, after the classic juice-bottle hero: one giant word in white, the
 * product standing in front of it (here, a phone showing a real launch post),
 * glossy icons floating around it, a juicy color per slide, dots and a
 * counter. Swipe, use the arrows or the keyboard; it moves on by itself until
 * someone interacts.
 */
function DropHero() {
  const reduceMotion = useReducedMotion() ?? false;
  const look = useLook();
  // The endless bobbing only runs while this hero is the one on screen.
  const still = reduceMotion || look !== "drop";
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [paused, setPaused] = useState(false);
  const [interacted, setInteracted] = useState(false);
  // Keyboard and screen reader users get a still carousel while they're in it.
  const [focusWithin, setFocusWithin] = useState(false);
  const slide = dropSlides[index];
  const post = getShowcasePost(slide.postId);
  const count = dropSlides.length;

  const go = useCallback(
    (next: number, dir?: number) => {
      setDirection(dir ?? (next > index ? 1 : -1));
      setIndex((next + count) % count);
    },
    [count, index],
  );

  // Advance on a timer while the Drop look is showing and nobody is interacting.
  const autoplay = look === "drop" && !reduceMotion && !paused && !interacted && !focusWithin;
  useEffect(() => {
    if (!autoplay) return;
    const timer = window.setTimeout(() => go(index + 1, 1), AUTO_MS);
    return () => window.clearTimeout(timer);
  }, [autoplay, go, index]);

  useEffect(() => {
    function onVisibility() {
      setPaused(document.hidden);
    }
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  // Fetch every slide's pictures once the page has settled, so no slide
  // arrives with an empty frame. The phone uses these exact URLs.
  useEffect(() => {
    if (look !== "drop") return;
    const timer = window.setTimeout(() => {
      for (const item of dropSlides) {
        const { author, media } = getShowcasePost(item.postId);
        for (const src of [author.avatar, media.src]) new Image().src = src;
      }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [look]);

  // Pointer parallax without re-rendering: motion values only.
  const px = useMotionValue(0);
  const py = useMotionValue(0);
  const sx = useSpring(px, { stiffness: 60, damping: 18 });
  const sy = useSpring(py, { stiffness: 60, damping: 18 });

  // Swipe on touch screens.
  const swipeStart = useRef<{ x: number; y: number } | null>(null);

  return (
    <section
      aria-roledescription="carousel"
      aria-label="What we get posted"
      className="relative isolate min-h-[100svh] overflow-hidden text-white select-none"
      onPointerMove={(event) => {
        if (event.pointerType !== "mouse" || reduceMotion) return;
        const rect = event.currentTarget.getBoundingClientRect();
        px.set(((event.clientX - rect.left) / rect.width) * 2 - 1);
        py.set(((event.clientY - rect.top) / rect.height) * 2 - 1);
      }}
      onPointerEnter={(event) => {
        if (event.pointerType === "mouse") setPaused(true);
      }}
      onPointerLeave={(event) => {
        if (event.pointerType === "mouse") setPaused(false);
      }}
      onFocus={() => setFocusWithin(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setFocusWithin(false);
      }}
      onPointerDown={(event) => {
        if (event.pointerType !== "mouse") swipeStart.current = { x: event.clientX, y: event.clientY };
      }}
      onPointerUp={(event) => {
        const start = swipeStart.current;
        swipeStart.current = null;
        if (!start) return;
        const dx = event.clientX - start.x;
        if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(event.clientY - start.y)) {
          setInteracted(true);
          go(index + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
        }
      }}
      onKeyDown={(event) => {
        if (event.key === "ArrowRight") {
          setInteracted(true);
          go(index + 1, 1);
        } else if (event.key === "ArrowLeft") {
          setInteracted(true);
          go(index - 1, -1);
        }
      }}
    >
      {/* The color field, with a soft light behind the phone and darker edges. */}
      <motion.div
        aria-hidden
        className="texture-noise absolute inset-0 -z-10"
        initial={false}
        animate={{ backgroundColor: slide.color }}
        transition={{ duration: 0.8, ease: [0.65, 0, 0.35, 1] }}
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_55%_50%_at_50%_48%,rgb(255_255_255/0.2),transparent_70%)]" />
        <motion.div
          className="absolute inset-0"
          initial={false}
          animate={{
            background: `radial-gradient(ellipse 120% 90% at 50% 45%, transparent 55%, ${slide.shade} 130%)`,
          }}
          transition={{ duration: 0.8 }}
        />
      </motion.div>

      <h1 className="sr-only">
        AGI 2027 gets launches, funding news and product drops posted by creators people already follow.
      </h1>

      {/* Icons behind the word. */}
      <Icons slide={slide} layer="back" sx={sx} sy={sy} reduceMotion={reduceMotion} still={still} />

      {/* The giant word. */}
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-[40%] -translate-y-1/2 sm:top-1/2">
        <AnimatePresence mode="popLayout" initial={false} custom={direction}>
          <motion.p
            key={slide.id}
            className="flex justify-center font-[family-name:var(--font-anton)] leading-[0.82] whitespace-nowrap uppercase"
            style={{ fontSize: wordSize(slide.word) }}
          >
            {slide.word.split("").map((letter, i) => (
              <span key={i} className="inline-block overflow-hidden pt-[0.06em] pb-[0.02em]">
                <motion.span
                  className="inline-block"
                  initial={reduceMotion ? { opacity: 0 } : { y: "105%" }}
                  animate={reduceMotion ? { opacity: 1 } : { y: "0%" }}
                  exit={reduceMotion ? { opacity: 0 } : { y: "-105%", transition: { duration: 0.35, ease: [0.65, 0, 0.35, 1], delay: i * 0.02 } }}
                  transition={{ ...snappy, delay: 0.08 + i * 0.04 }}
                >
                  {letter}
                </motion.span>
              </span>
            ))}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* The phone. */}
      <div className="pointer-events-none absolute inset-x-0 top-[40%] flex -translate-y-1/2 justify-center [perspective:1400px] sm:top-1/2">
        <AnimatePresence mode="popLayout" initial={false} custom={direction}>
          <motion.div
            key={slide.id}
            custom={direction}
            variants={{
              enter: (dir: number) =>
                reduceMotion ? { opacity: 0 } : { x: `${dir * 60}vw`, rotateY: dir * -40, rotateZ: dir * 10, opacity: 0 },
              center: { x: 0, rotateY: -12, rotateZ: -5, opacity: 1 },
              exit: (dir: number) =>
                reduceMotion ? { opacity: 0 } : { x: `${dir * -60}vw`, rotateY: dir * 40, rotateZ: dir * -10, opacity: 0 },
            }}
            initial="enter"
            animate="center"
            exit="exit"
            transition={smooth}
            className="[transform-style:preserve-3d]"
          >
            <Floaty disabled={still}>
              <Phone post={post} />
            </Floaty>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Icons in front, some soft-focused as if close to the camera. */}
      <Icons slide={slide} layer="front" sx={sx} sy={sy} reduceMotion={reduceMotion} still={still} />

      {/* Caption, calls to action and controls. */}
      <div className="absolute inset-x-0 bottom-0 z-10 mx-auto max-w-[90rem] px-5 pb-3 sm:px-8 sm:pb-6 lg:px-10">
        <div className="max-w-[24rem]">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={slide.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6, transition: { duration: 0.15 } }}
              transition={snappy}
              aria-live={autoplay ? "off" : "polite"}
            >
              <p className="text-[19px] font-semibold tracking-[-0.02em] sm:text-[21px]">{slide.title}</p>
              <p className="mt-1 text-[15px] leading-snug text-white/88">{slide.body}</p>
            </motion.div>
          </AnimatePresence>
          {/* One lasting link whose text changes, so keyboard focus survives a slide change. */}
          <p className="mt-1.5 flex flex-wrap items-center gap-x-3 text-[13px] text-white/80">
            <a
              href={post.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-6 items-center gap-1 font-semibold text-white/90 underline decoration-white/40 underline-offset-[3px] transition-colors hover:text-white hover:decoration-white"
            >
              <motion.span key={post.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
                Example: {post.author.name}&rsquo;s post on X
              </motion.span>
              <ArrowUpRight aria-hidden className="size-3.5" />
            </a>
            {Object.keys(post.stats).length > 0 ? <span>Numbers as of {formatUtcDate(STATS_AS_OF)}</span> : null}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href="/book"
              className="pressable inline-flex h-11 items-center gap-2 rounded-full bg-white px-5 text-[14px] font-semibold text-[#16120f] shadow-[0_10px_30px_rgb(0_0_0/0.2)] transition-transform duration-200 ease-snap hover:-translate-y-0.5"
            >
              Book a campaign
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/apply"
              className="pressable inline-flex h-11 items-center rounded-full px-5 text-[14px] font-semibold ring-1 ring-white/70 transition-colors duration-200 ease-snap ring-inset hover:bg-white/15"
            >
              Apply as a creator
            </Link>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between gap-3 sm:mt-3">
          <Dots index={index} onSelect={(i) => { setInteracted(true); go(i); }} running={autoplay} />
        <div className="flex items-center gap-2 sm:gap-3">
          <p className="font-[family-name:var(--font-anton)] text-[19px] leading-none tracking-[0.04em] tabular-nums sm:text-[22px]">
            <span aria-hidden>{String(index + 1).padStart(2, "0")}</span>
            <span aria-hidden className="mx-1.5 text-white/60">/</span>
            <span aria-hidden className="text-white/60">{String(count).padStart(2, "0")}</span>
            <span className="sr-only">
              Slide {index + 1} of {count}: {slide.title}
            </span>
          </p>
          <button
            type="button"
            onClick={() => {
              setInteracted(true);
              go(index - 1, -1);
            }}
            className="pressable inline-flex size-11 cursor-pointer items-center justify-center rounded-full ring-1 ring-white/60 transition-colors ring-inset hover:bg-white hover:text-[#16120f]"
            aria-label="Previous slide"
          >
            <ArrowLeft className="size-4" />
          </button>
          <button
            type="button"
            onClick={() => {
              setInteracted(true);
              go(index + 1, 1);
            }}
            className="pressable inline-flex size-11 cursor-pointer items-center justify-center rounded-full bg-white text-[#16120f] transition-transform hover:-translate-y-0.5"
            aria-label="Next slide"
          >
            <ArrowRight className="size-4" />
          </button>
        </div>
        </div>
      </div>
      <div data-hero-end aria-hidden className="absolute bottom-0 left-0 h-px w-px" />
    </section>
  );
}

function Dots({ index, onSelect, running }: { index: number; onSelect: (i: number) => void; running: boolean }) {
  return (
    <div className="-ml-1 flex items-center gap-0.5" role="group" aria-label="Choose a slide">
      {dropSlides.map((slide, i) => (
        <button
          key={slide.id}
          type="button"
          onClick={() => onSelect(i)}
          aria-label={`Show ${slide.title}`}
          aria-current={i === index ? "true" : undefined}
          className="group flex h-11 cursor-pointer items-center px-1"
        >
          <span
            className={cn(
              "relative block h-2 overflow-hidden rounded-full bg-white/45 transition-[width,background-color] duration-500 ease-spring-smooth group-hover:bg-white/80",
              i === index ? "w-9" : "w-2",
            )}
          >
            {i === index ? (
              <motion.span
                key={`${slide.id}-${running}`}
                className="absolute inset-y-0 left-0 block w-full origin-left rounded-full bg-white"
                initial={{ scaleX: running ? 0 : 1 }}
                animate={{ scaleX: 1 }}
                transition={running ? { duration: AUTO_MS / 1000, ease: "linear" } : { duration: 0 }}
              />
            ) : null}
          </span>
        </button>
      ))}
    </div>
  );
}

/** A slow bob so the phone feels like it's hanging in the air. */
function Floaty({ children, disabled }: { children: React.ReactNode; disabled: boolean }) {
  return (
    <motion.div
      animate={disabled ? undefined : { y: [0, -12, 0], rotateZ: [0, 1.2, 0] }}
      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
    >
      {children}
    </motion.div>
  );
}

function Icons({
  slide,
  layer,
  sx,
  sy,
  reduceMotion,
  still,
}: {
  slide: DropSlide;
  layer: "back" | "front";
  sx: MotionValue<number>;
  sy: MotionValue<number>;
  reduceMotion: boolean;
  still: boolean;
}) {
  const icons = slide.icons.filter((icon) => (layer === "front" ? icon.depth >= 0.4 : icon.depth < 0.4));
  return (
    <div aria-hidden className={cn("pointer-events-none absolute inset-0", layer === "front" ? "z-[5]" : "-z-[5]")}>
      <AnimatePresence initial={false}>
        {icons.map((icon, i) => (
          <FloatingIcon
            key={`${slide.id}-${icon.name}-${i}`}
            icon={icon}
            index={i}
            sx={sx}
            sy={sy}
            reduceMotion={reduceMotion}
            still={still}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

function FloatingIcon({
  icon,
  index,
  sx,
  sy,
  reduceMotion,
  still,
}: {
  icon: DropIcon;
  index: number;
  sx: MotionValue<number>;
  sy: MotionValue<number>;
  reduceMotion: boolean;
  still: boolean;
}) {
  const reach = 10 + icon.depth * 40;
  const x = useTransform(sx, (value) => value * reach);
  const y = useTransform(sy, (value) => value * reach * 0.7);
  const blur = icon.depth >= 0.9 ? 9 : icon.depth >= 0.5 ? 1.5 : 0;
  return (
    <div
      className={cn(
        "absolute top-(--py) left-(--px) sm:top-(--dy) sm:left-(--dx)",
        icon.desktopOnly && "hidden sm:block",
      )}
      style={
        {
          "--dx": `${icon.x}%`,
          "--dy": `${icon.y}%`,
          "--px": `${icon.phone?.x ?? icon.x}%`,
          "--py": `${icon.phone?.y ?? icon.y}%`,
          width: `${icon.size}vmin`,
        } as React.CSSProperties
      }
    >
    <motion.div
      style={{ x, y }}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.4, rotate: icon.rotate - 40 }}
      animate={reduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, rotate: icon.rotate }}
      exit={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.6, transition: { duration: 0.25 } }}
      transition={{ ...snappy, delay: 0.12 + index * 0.06 }}
    >
      <motion.img
        src={`/art/icons/${icon.name}.webp`}
        alt=""
        draggable={false}
        className="block h-auto w-full -translate-x-1/2 -translate-y-1/2 drop-shadow-[0_18px_24px_rgb(0_0_0/0.25)]"
        style={{ filter: blur ? `blur(${blur}px)` : undefined }}
        animate={still ? undefined : { y: [0, -10 - icon.depth * 8, 0], rotate: [0, icon.depth * 6, 0] }}
        transition={{ duration: 4.5 + index * 0.7, repeat: Infinity, ease: "easeInOut" }}
      />
    </motion.div>
    </div>
  );
}

/** The product: a phone showing a real launch post, drawn as X's post page. */
function Phone({ post }: { post: ShowcasePost }) {
  const { author, media, stats } = post;
  return (
    <div
      className="relative w-[292px] origin-center scale-[0.5] rounded-[2.6rem] min-[420px]:scale-[0.58] sm:scale-[0.72] md:scale-[0.8] lg:scale-[0.9] xl:scale-100 [@media(max-height:760px)_and_(min-width:640px)]:scale-[0.78] bg-[linear-gradient(145deg,#3a3a3c,#0d0d0e_45%,#2a2a2c)] p-[9px] shadow-[0_2px_0_1px_rgb(255_255_255/0.12)_inset,0_40px_80px_-20px_rgb(0_0_0/0.55),0_18px_36px_-12px_rgb(0_0_0/0.4)]"
      style={{ aspectRatio: "9 / 19.2" }}
    >
      <div className="relative flex h-full flex-col overflow-hidden rounded-[2.1rem] bg-[#fdfcfa] text-[#0f1419]">
        <div className="absolute top-2 left-1/2 h-[22px] w-[34%] -translate-x-1/2 rounded-full bg-black" />
        <div className="flex h-11 items-end justify-between px-6 pb-1 text-[11px] font-semibold">
          <span>9:41</span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-3 rounded-[2px] bg-current" />
            <span className="h-2.5 w-5 rounded-[3px] border border-current p-px">
              <span className="block h-full w-3/4 rounded-[1px] bg-current" />
            </span>
          </span>
        </div>
        <div className="flex items-center gap-2 border-b border-black/8 px-4 py-2 text-[13px] font-bold">
          <ArrowLeft className="size-4" />
          Post
        </div>
        <div className="flex-1 overflow-hidden px-4 pt-3 text-left">
          <div className="flex items-center gap-2.5">
            <PostAvatar author={author} className="size-9" />
            <span className="min-w-0 leading-tight">
              <span className="flex items-center gap-1 text-[13px] font-bold">
                <span className="truncate">{author.name}</span>
                <VerifiedBadge badge={author.badge} className="size-3.5 shrink-0" />
              </span>
              <span className="block text-[11.5px] text-[#536471]">@{author.handle}</span>
            </span>
          </div>
          <PostText
            post={post}
            max={250}
            className="mt-2 text-[12.5px] leading-[1.38]"
            accentClassName="text-[#1d9bf0]"
            more={<span className="text-[#1d9bf0]"> Show more</span>}
          />
          <div
            className="relative mt-2.5 overflow-hidden rounded-xl bg-black/5 ring-1 ring-black/8"
            style={{ aspectRatio: mediaAspect(media) }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- preloaded by URL for the slide change */}
            <img
              src={media.src}
              alt={media.alt}
              width={media.width}
              height={media.height}
              decoding="async"
              draggable={false}
              className="size-full object-cover"
              style={{ objectPosition: media.focus }}
            />
          </div>
          {media.kind === "link" && media.from ? (
            <p className="mt-1 text-[10px] text-[#536471]">From {media.from}</p>
          ) : null}
          <p className="mt-2 text-[10.5px] text-[#536471]">
            {formatUtcDate(post.postedAt)}
            {stats.views ? (
              <>
                {" · "}
                <span className="font-semibold text-[#0f1419]">{stats.views}</span> Views
              </>
            ) : null}
          </p>
          <div className="mt-2 flex justify-between border-t border-black/8 pt-2 text-[10.5px] text-[#536471]">
            <PhoneStat icon={MessageCircle} value={stats.replies} />
            <PhoneStat icon={Repeat2} value={stats.reposts} />
            <PhoneStat icon={Heart} value={stats.likes} className={stats.likes ? "text-[#f91880] [&_svg]:fill-current" : undefined} />
            <PhoneStat icon={Bookmark} value={stats.bookmarks} />
            <Share2 className="size-3.5" />
          </div>
          <div className="mt-3 flex items-center gap-2 border-t border-black/8 pt-3">
            <span className="size-7 shrink-0 rounded-full bg-[#e7ecf0]" />
            <span className="flex-1 text-[11.5px] text-[#536471]">Post your reply</span>
            <span className="rounded-full bg-[#0f1419] px-3 py-1 text-[10.5px] font-bold text-white">Reply</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PhoneStat({
  icon: Icon,
  value,
  className,
}: {
  icon: typeof Heart;
  value?: string;
  className?: string;
}) {
  return (
    <span className={cn("flex items-center gap-1", className)}>
      <Icon className="size-3.5" />
      {value}
    </span>
  );
}

export { DropHero };
