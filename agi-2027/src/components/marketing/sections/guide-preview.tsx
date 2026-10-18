"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { Check } from "lucide-react";

import { springMove, springPop } from "@/components/creator/motion";
import { PhoneFrame } from "./phone-frame";

/*
 * How the site works for a creator, from applying to getting paid. The words
 * follow /apply, the perks beside the phones and the campaign loop in
 * SPEC.md, so change them together.
 */
export const GUIDE_STEPS = [
  { title: "Apply", body: "About five minutes. Share your three best posts." },
  { title: "Get approved", body: "A person reads every application. We email you the answer." },
  { title: "Claim a drop", body: "New drops land in your portal and on Telegram. Tap Claim." },
  { title: "Post in the window", body: "The brief, your angle, the assets and the exact post window." },
  { title: "Send proof, get paid", body: "Paste your post link. Once it's approved, you're paid per post." },
] as const;

/** What a screen reader hears for this phone, in the same form as the claim phone's. */
export const GUIDE_PREVIEW_LABEL =
  "A creator's phone: how it works, in five steps. Apply, get approved, claim a drop, post in the window, then send proof and get paid.";

const FIRST_TICK = 600;
const TICK_EVERY = 480;

/**
 * Jesse's phone with the guide. The first time it scrolls into view the steps
 * tick off one by one while the current step lifts, and the bar on top fills.
 * It plays once, like every reveal on the site; with reduced motion every
 * step simply shows as done.
 */
function GuidePreview({ className }: { className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  const inView = useInView(host, { amount: 0.6, once: true });
  const reduce = useReducedMotion();
  const [done, setDone] = useState(0);

  useEffect(() => {
    // Reduced motion shows every step done. It's set here, not while
    // rendering: the server can't know the setting, so the first render has
    // to match its untouched list.
    if (reduce) {
      const end = window.setTimeout(() => setDone(GUIDE_STEPS.length), 0);
      return () => window.clearTimeout(end);
    }
    if (!inView) return;
    const ticks = GUIDE_STEPS.map((_, index) =>
      window.setTimeout(() => setDone(index + 1), FIRST_TICK + index * TICK_EVERY),
    );
    return () => ticks.forEach((tick) => window.clearTimeout(tick));
  }, [inView, reduce]);

  const last = GUIDE_STEPS.length - 1;
  // The step being worked on: the next one, or the last once it's all done.
  const current = Math.min(done, last);
  const move = reduce ? { duration: 0 } : springMove;
  const pop = reduce ? { duration: 0 } : springPop;

  return (
    <PhoneFrame
      ref={host}
      className={className}
      label={GUIDE_PREVIEW_LABEL}
    >
      <div className="px-[18px] pt-[14px]">
        <p className="text-[12px] font-semibold text-[#6b635c]">Hi Jesse</p>
        <p className="mt-px text-[24px] leading-tight font-bold tracking-[-0.045em]">How it works</p>
      </div>

      <div className="mx-[18px] mt-[12px] flex gap-[4px]">
        {GUIDE_STEPS.map((step, index) => (
          <span key={step.title} className="h-[4px] flex-1 overflow-hidden rounded-full bg-[#e6e1db]">
            <motion.span
              className="block h-full rounded-full bg-[#1f9d55]"
              style={{ originX: 0 }}
              initial={false}
              animate={{ scaleX: index < done ? 1 : 0 }}
              transition={move}
            />
          </span>
        ))}
      </div>

      <ol className="mx-[8px] mt-[10px] flex flex-1 flex-col pb-[22px]">
        {GUIDE_STEPS.map((step, index) => {
          const isDone = index < done;
          const isCurrent = index === current;
          return (
            <li key={step.title} className="relative flex-1">
              {/* The line down to the next step fills in once this one is done. */}
              {index < last ? (
                <span className="absolute top-[40px] -bottom-[11px] left-[22px] w-[2px] overflow-hidden rounded-full bg-[#e6e1db]">
                  <motion.span
                    className="block h-full w-full bg-[#1f9d55]"
                    style={{ originY: 0 }}
                    initial={false}
                    animate={{ scaleY: isDone ? 1 : 0 }}
                    transition={move}
                  />
                </span>
              ) : null}
              <div className="relative flex gap-[11px] px-[10px] py-[10px]">
                {/* The current step lifts onto a white card. */}
                <motion.span
                  className="absolute inset-0 rounded-[1.1rem] bg-white shadow-[0_1px_2px_rgb(0_0_0/0.06),0_12px_26px_-14px_rgb(0_0_0/0.25)]"
                  initial={false}
                  animate={isCurrent ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.94 }}
                  transition={move}
                />
                <span
                  className={`relative mt-px flex size-[26px] shrink-0 items-center justify-center rounded-full text-[11.5px] font-bold tabular-nums transition-colors duration-300 ${
                    isDone
                      ? "bg-[#1f9d55] text-white"
                      : isCurrent
                        ? "bg-[#16120f] text-white"
                        : "bg-white text-[#9a918a] ring-1 ring-[#e6e1db]"
                  }`}
                >
                  {isDone ? (
                    <motion.span key="done" initial={reduce ? false : { scale: 0.3 }} animate={{ scale: 1 }} transition={pop}>
                      <Check className="size-[14px]" strokeWidth={3.2} />
                    </motion.span>
                  ) : (
                    index + 1
                  )}
                </span>
                <span className="relative min-w-0 pt-[2px]">
                  <span
                    className={`block text-[14.5px] leading-tight font-bold tracking-[-0.02em] ${isDone || isCurrent ? "text-[#16120f]" : "text-[#4a443e]"}`}
                  >
                    {step.title}
                  </span>
                  <span className="mt-[3px] block text-[12px] leading-[1.35] text-[#6b635c]">{step.body}</span>
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </PhoneFrame>
  );
}

export { GuidePreview };
