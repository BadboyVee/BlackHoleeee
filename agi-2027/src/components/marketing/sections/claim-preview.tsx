"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useReducedMotion } from "motion/react";
import { BadgeDollarSign, Check, Clock, House, Layers, Megaphone, Sparkles, UserRound, Wallet } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { springMove, springPop } from "@/components/creator/motion";
import { PostAvatar, VerifiedBadge } from "@/components/marketing/x-post";
import { getShowcasePost } from "@/lib/showcase-posts";
import { formatUtcDay, formatUtcTime } from "@/lib/time";
import { PhoneFrame } from "./phone-frame";

/*
 * A campaign the owner really ran: Kled's V3 launch on 30 Sep 2026. The name,
 * picture, video still and launch time all come from Kled's own post, and the
 * angle is a line from it. No pay amount or slot count: the card shows only
 * what is true of every campaign (posted on X, paid per post).
 */
const KLED_POST_ID = "2105311618284527767";
const kled = getShowcasePost(KLED_POST_ID);
/** The launch slot. Kled's post went out at 14:59:39, just before it. */
export const KLED_LAUNCH_AT = "2026-09-30T15:00:00Z";

export const CLAIM_PREVIEW = {
  creator: "Jesse",
  brand: kled.author.name,
  title: "Kled V3 launch day",
  launch: `Launch ${formatUtcDay(KLED_LAUNCH_AT)}, ${formatUtcTime(KLED_LAUNCH_AT)}`,
  angle: "Any consumer dataset, collected in under 72 hours",
};

/** What a screen reader hears for this phone. */
export const CLAIM_PREVIEW_LABEL = `A creator's phone: ${CLAIM_PREVIEW.creator} claims the ${CLAIM_PREVIEW.title} campaign from ${CLAIM_PREVIEW.brand} in one tap.`;

/** The creator app's own tab bar, as in `creator-nav.tsx`. */
const TABS = [
  { label: "Home", icon: House },
  { label: "Campaigns", icon: Megaphone },
  { label: "Mine", icon: Layers },
  { label: "Earnings", icon: Wallet },
  { label: "Profile", icon: UserRound },
];

/*
 * The claim, in steps: the finger glides onto Claim, presses it, and the
 * button turns into "You're in" as the confetti pops. Times are from the
 * moment the phone is in view.
 */
type Phase = "idle" | "approach" | "press" | "done";
const TIMELINE: [Phase, number][] = [
  ["approach", 450],
  ["press", 1150],
  ["done", 1400],
];

/** Where the fingertip lands on the button, right of the word so it never hides it. */
const TOUCH = "top-1/2 left-[74%]";

/**
 * Jesse's phone with the Kled V3 drop. When it scrolls into view a finger
 * taps Claim, the button turns into "You're in" and a little burst of
 * confetti pops. It replays each time it comes back into view; with reduced
 * motion the phone simply shows the end: "You're in".
 */
function ClaimPreview({ className }: { className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  const inView = useInView(host, { amount: 0.6 });
  const reduce = useReducedMotion();
  const [phase, setPhase] = useState<Phase>("idle");

  useEffect(() => {
    // Reduced motion skips the story and shows how it ends. It's set here, not
    // while rendering: the server can't know the setting, so the first render
    // has to match its "Claim".
    if (reduce) {
      const end = window.setTimeout(() => setPhase("done"), 0);
      return () => window.clearTimeout(end);
    }
    if (!inView) {
      const reset = window.setTimeout(() => setPhase("idle"), 400);
      return () => window.clearTimeout(reset);
    }
    const steps = TIMELINE.map(([next, at]) => window.setTimeout(() => setPhase(next), at));
    return () => steps.forEach((step) => window.clearTimeout(step));
  }, [inView, reduce]);

  const claimed = phase === "done";
  const pressing = phase === "press";
  const touched = !reduce && (pressing || claimed);

  return (
    <PhoneFrame ref={host} className={className} label={CLAIM_PREVIEW_LABEL}>
      <div className="px-[18px] pt-[14px]">
        <p className="text-[12px] font-semibold text-[#6b635c]">Good morning, {CLAIM_PREVIEW.creator}</p>
        <p className="mt-px text-[24px] leading-tight font-bold tracking-[-0.045em]">New drops</p>
      </div>

      <div className="relative mx-[12px] mt-[12px] rounded-[1.5rem] bg-white p-[14px] shadow-[0_1px_2px_rgb(0_0_0/0.06),0_14px_30px_-14px_rgb(0_0_0/0.22)]">
        <div className="flex items-center gap-[10px]">
          <PostAvatar author={kled.author} className="size-[38px] ring-1 ring-black/10" />
          <span className="min-w-0 leading-tight">
            <span className="flex items-center gap-[3px] text-[12px] font-semibold text-[#6b635c]">
              {CLAIM_PREVIEW.brand}
              <VerifiedBadge badge={kled.author.badge} className="size-[13px] shrink-0" />
            </span>
            <span className="block text-[15px] font-bold tracking-[-0.025em]">{CLAIM_PREVIEW.title}</span>
          </span>
        </div>

        <div className="relative mt-[12px] overflow-hidden rounded-[0.9rem] bg-black ring-1 ring-black/5" style={{ aspectRatio: "16 / 9" }}>
          {/* eslint-disable-next-line @next/next/no-img-element -- a small still inside a scaled mockup */}
          <img
            src={kled.media.src}
            alt=""
            width={kled.media.width}
            height={kled.media.height}
            loading="lazy"
            decoding="async"
            draggable={false}
            className="size-full object-cover"
            style={{ objectPosition: "50% 28%" }}
          />
          <span className="absolute top-[8px] left-[8px] rounded-full bg-[#e9f9d4] px-[7px] py-[2px] text-[10px] font-bold tracking-[0.04em] text-[#3d6a00] shadow-[0_2px_6px_rgb(0_0_0/0.25)]">
            NEW
          </span>
        </div>

        <p className="mt-[11px] flex items-center gap-[6px] text-[11.5px] font-medium text-[#4a443e]">
          <Clock className="size-[13px] shrink-0 text-[#6b635c]" />
          {CLAIM_PREVIEW.launch}
        </p>
        <div className="mt-[8px] flex gap-[6px] text-[11px] font-semibold text-[#4a443e]">
          <span className="flex items-center gap-[5px] rounded-full bg-[#f3f0ec] px-[9px] py-[4px]">
            <XLogo className="size-[11px]" />
            Post on X
          </span>
          <span className="flex items-center gap-[5px] rounded-full bg-[#f3f0ec] px-[9px] py-[4px]">
            <BadgeDollarSign className="size-[13px]" />
            Paid per post
          </span>
        </div>

        <div className="relative mt-[13px]">
          <motion.div
            initial={false}
            animate={{ scale: pressing ? 0.95 : 1 }}
            transition={springPop}
            className={`relative flex h-[44px] items-center justify-center overflow-hidden rounded-full text-[15px] font-bold text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.16),0_8px_18px_-10px_rgb(0_0_0/0.5)] transition-colors duration-300 ${
              claimed ? "bg-[#1f9d55]" : "bg-[#16120f]"
            }`}
          >
            {/* The press spreads from under the fingertip, like ink. */}
            {touched ? (
              <motion.span
                className={`absolute ${TOUCH} -mt-[22px] -ml-[22px] size-[44px] rounded-full bg-white/35`}
                initial={{ scale: 0.3, opacity: 1 }}
                animate={{ scale: 6, opacity: 0 }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              />
            ) : null}
            <AnimatePresence mode="wait" initial={false}>
              {claimed ? (
                <motion.span
                  key="in"
                  className="relative flex items-center gap-1.5"
                  initial={reduce ? false : { opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={springMove}
                >
                  <Check className="size-4" strokeWidth={3} /> You&apos;re in
                </motion.span>
              ) : (
                <motion.span
                  key="claim"
                  className="relative"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={reduce ? { opacity: 0 } : { opacity: 0, y: -8, transition: { duration: 0.15 } }}
                >
                  Claim
                </motion.span>
              )}
            </AnimatePresence>
          </motion.div>

          <Confetti show={claimed && !reduce} />

          {/* The fingertip: glides in from the bottom right, presses, lifts away. */}
          <AnimatePresence>
            {!reduce && (phase === "approach" || pressing) ? (
              <motion.span
                key="finger"
                className={`pointer-events-none absolute ${TOUCH} z-10 -mt-[17px] -ml-[17px] size-[34px] rounded-full bg-white/55 shadow-[0_8px_20px_-4px_rgb(0_0_0/0.4),inset_0_0_0_1.5px_rgb(255_255_255/0.9)] backdrop-blur-[3px]`}
                initial={{ opacity: 0, x: 40, y: 64, scale: 1.2 }}
                animate={pressing ? { opacity: 1, x: 0, y: 1, scale: 0.8 } : { opacity: 1, x: 0, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 1.25, transition: { duration: 0.25 } }}
                transition={{ type: "spring", stiffness: 260, damping: 24 }}
              />
            ) : null}
          </AnimatePresence>
        </div>
      </div>

      <p className="mx-[12px] mt-[10px] flex items-start gap-[8px] rounded-[1.1rem] bg-white/75 px-[12px] py-[10px] text-[11.5px] leading-snug text-[#4a443e] ring-1 ring-black/[0.04]">
        <Sparkles className="mt-px size-[14px] shrink-0 text-[#c27a00]" />
        <span>
          <span className="font-semibold text-[#16120f]">Your angle:</span> {CLAIM_PREVIEW.angle}
        </span>
      </p>

      <div className="mt-auto flex justify-between border-t border-black/[0.06] bg-white/85 px-[14px] pt-[8px] pb-[22px]">
        {TABS.map(({ label, icon: Icon }, index) => (
          <span
            key={label}
            className={`flex w-[44px] flex-col items-center gap-[3px] text-[9.5px] font-semibold ${index === 0 ? "text-[#16120f]" : "text-[#9a918a]"}`}
          >
            <Icon className="size-[18px]" strokeWidth={index === 0 ? 2.4 : 2} />
            {label}
          </span>
        ))}
      </div>
    </PhoneFrame>
  );
}

/*
 * A fixed spread (the golden angle) so the burst looks placed, never
 * random: strips, squares and dots that pop out, then drift down.
 */
const CONFETTI_COLORS = ["#ff2e8a", "#ffd23f", "#2ec27e", "#4da3ff", "#ff7a1a", "#9a6bff"];
const CONFETTI = Array.from({ length: 22 }, (_, index) => {
  const angle = (index * 137.508 * Math.PI) / 180;
  const distance = 52 + ((index * 29) % 58);
  const shape = index % 3;
  return {
    x: Math.round(Math.cos(angle) * distance * 1.35),
    y: Math.round(Math.sin(angle) * distance * 0.8 - 18),
    width: shape === 0 ? 4 : shape === 1 ? 7 : 6,
    height: shape === 0 ? 10 : shape === 1 ? 7 : 6,
    radius: shape === 2 ? 999 : 1.5,
    rotate: ((index * 83) % 420) - 210,
    color: CONFETTI_COLORS[index % CONFETTI_COLORS.length],
    delay: (index % 5) * 0.02,
  };
});

function Confetti({ show }: { show: boolean }) {
  return (
    <AnimatePresence>
      {show
        ? CONFETTI.map((piece, index) => (
            <motion.span
              key={index}
              className="pointer-events-none absolute top-1/2 left-1/2 z-10 block"
              style={{
                width: piece.width,
                height: piece.height,
                marginLeft: -piece.width / 2,
                marginTop: -piece.height / 2,
                borderRadius: piece.radius,
                backgroundColor: piece.color,
              }}
              initial={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 0.4 }}
              animate={{
                x: [0, piece.x, piece.x * 1.08],
                y: [0, piece.y, piece.y + 46],
                rotate: piece.rotate,
                scale: 1,
                opacity: [1, 1, 0],
              }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 1.15,
                times: [0, 0.4, 1],
                ease: [0.22, 1, 0.36, 1],
                delay: piece.delay,
                scale: { ...springPop, delay: piece.delay },
              }}
            />
          ))
        : null}
    </AnimatePresence>
  );
}

export { ClaimPreview };
