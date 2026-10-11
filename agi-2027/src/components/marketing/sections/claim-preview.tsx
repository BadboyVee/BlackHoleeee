"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useReducedMotion } from "motion/react";
import { Check, Clock, Sparkles } from "lucide-react";

/**
 * A creator's phone showing a real-looking campaign card. When it scrolls into
 * view, a finger "taps" Claim: the slot counter ticks down, the button turns
 * into "You're in" and a little burst of confetti pops. It replays each time
 * it comes back into view.
 */
function ClaimPreview({ className }: { className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  const inView = useInView(host, { amount: 0.6 });
  const reduce = useReducedMotion();
  const [claimed, setClaimed] = useState(false);
  const [tapping, setTapping] = useState(false);

  useEffect(() => {
    if (!inView) {
      const reset = window.setTimeout(() => setClaimed(false), 400);
      return () => window.clearTimeout(reset);
    }
    if (reduce) {
      const show = window.setTimeout(() => setClaimed(true), 600);
      return () => window.clearTimeout(show);
    }
    const tap = window.setTimeout(() => setTapping(true), 1100);
    const done = window.setTimeout(() => {
      setTapping(false);
      setClaimed(true);
    }, 1450);
    return () => {
      window.clearTimeout(tap);
      window.clearTimeout(done);
    };
  }, [inView, reduce]);

  const taken = claimed ? 14 : 13;
  const total = 20;

  return (
    <div ref={host} className={className}>
      <div className="relative mx-auto w-[min(19rem,78vw)] rounded-[2.6rem] bg-[linear-gradient(145deg,#3a3a3c,#0d0d0e_45%,#2a2a2c)] p-[9px] shadow-[0_2px_0_1px_rgb(255_255_255/0.12)_inset,0_40px_80px_-24px_rgb(0_0_0/0.5)]">
        <div className="relative overflow-hidden rounded-[2.1rem] bg-[#f7f5f2] text-[#16120f]" style={{ aspectRatio: "9 / 17" }}>
          <div className="absolute top-2 left-1/2 h-[22px] w-[34%] -translate-x-1/2 rounded-full bg-black" />
          <div className="flex h-11 items-end justify-between px-6 pb-1 text-[11px] font-semibold">
            <span>9:41</span>
            <span className="h-2.5 w-5 rounded-[3px] border border-current p-px">
              <span className="block h-full w-3/4 rounded-[1px] bg-current" />
            </span>
          </div>
          <div className="px-4 pt-3">
            <p className="text-[11px] font-semibold text-[#6b635c]">Good morning, Amara</p>
            <p className="text-[20px] font-bold tracking-[-0.04em]">New drops</p>
          </div>

          <div className="mx-3 mt-3 rounded-[1.4rem] bg-white p-4 shadow-[0_1px_2px_rgb(0_0_0/0.06),0_12px_28px_-12px_rgb(0_0_0/0.18)]">
            <div className="flex items-center gap-2.5">
              <span className="flex size-9 items-center justify-center rounded-xl bg-[#5b2ee8] text-[11px] font-bold text-white">
                NA
              </span>
              <span className="leading-tight">
                <span className="block text-[12px] font-semibold text-[#6b635c]">Nebula AI</span>
                <span className="block text-[14px] font-bold tracking-[-0.02em]">Nebula 2.0 launch day</span>
              </span>
              <span className="ml-auto rounded-full bg-[#e9f9d4] px-2 py-0.5 text-[10px] font-bold text-[#3d6a00]">NEW</span>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <span>
                <span className="block text-[10px] font-semibold text-[#6b635c]">You earn</span>
                <span className="text-[28px] leading-none font-bold tracking-[-0.05em]">
                  250 <span className="text-[13px] tracking-normal text-[#6b635c]">USDC</span>
                </span>
              </span>
              <span className="text-right">
                <span className="block text-[10px] font-semibold text-[#6b635c]">Slots left</span>
                <span className="relative inline-flex h-7 items-end overflow-hidden text-[22px] leading-none font-bold tracking-[-0.04em] tabular-nums">
                  <AnimatePresence mode="popLayout" initial={false}>
                    <motion.span
                      key={total - taken}
                      initial={{ y: "100%", opacity: 0 }}
                      animate={{ y: "0%", opacity: 1 }}
                      exit={{ y: "-100%", opacity: 0 }}
                      transition={{ type: "spring", stiffness: 500, damping: 26 }}
                    >
                      {total - taken}
                    </motion.span>
                  </AnimatePresence>
                  <span className="ml-0.5 text-[13px] text-[#6b635c]">/{total}</span>
                </span>
              </span>
            </div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#efebe6]">
              <motion.div
                className="h-full w-full rounded-full bg-[#16120f]"
                style={{ originX: 0 }}
                initial={false}
                animate={{ scaleX: taken / total }}
                transition={{ type: "spring", stiffness: 200, damping: 24 }}
              />
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-[11px] text-[#6b635c]">
              <Clock className="size-3" aria-hidden />
              Post window Tue 3 Nov, 16:00 to 20:00 UTC
            </p>

            <div className="relative mt-4">
              <motion.div
                animate={tapping ? { scale: 0.95 } : { scale: 1 }}
                transition={{ type: "spring", stiffness: 500, damping: 18 }}
                className={`flex h-11 items-center justify-center gap-2 rounded-full text-[14px] font-bold transition-colors duration-300 ${
                  claimed ? "bg-[#1f9d55] text-white" : "bg-[#16120f] text-white"
                }`}
              >
                <AnimatePresence mode="wait" initial={false}>
                  {claimed ? (
                    <motion.span
                      key="in"
                      className="flex items-center gap-1.5"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                    >
                      <Check className="size-4" aria-hidden /> You&apos;re in
                    </motion.span>
                  ) : (
                    <motion.span key="claim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, y: -8 }}>
                      Claim
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
              <Confetti show={claimed && !reduce} />
              {/* The "finger". */}
              <AnimatePresence>
                {!claimed && !reduce && inView ? (
                  <motion.span
                    aria-hidden
                    className="pointer-events-none absolute top-1/2 left-1/2 size-10 rounded-full bg-white/70 ring-2 ring-black/10 backdrop-blur"
                    initial={{ opacity: 0, x: 40, y: 40, scale: 1 }}
                    animate={tapping ? { opacity: 1, x: -20, y: -20, scale: 0.8 } : { opacity: 1, x: -10, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.4 }}
                    transition={{ type: "spring", stiffness: 300, damping: 22 }}
                  />
                ) : null}
              </AnimatePresence>
            </div>
          </div>

          <div className="mx-3 mt-3 flex items-center gap-2 rounded-[1.2rem] bg-white/70 p-3 text-[11.5px] text-[#4a443e]">
            <Sparkles className="size-3.5 text-[#c27a00]" aria-hidden />
            Your angle: the 10-minute build
          </div>
        </div>
      </div>
    </div>
  );
}

function Confetti({ show }: { show: boolean }) {
  const pieces = Array.from({ length: 14 }, (_, i) => i);
  const colors = ["#ff2e8a", "#ffd23f", "#2ec27e", "#4da3ff", "#ff7a1a", "#9a6bff"];
  return (
    <AnimatePresence>
      {show
        ? pieces.map((i) => {
            const angle = (i / pieces.length) * Math.PI * 2;
            const distance = 60 + (i % 3) * 22;
            return (
              <motion.span
                key={i}
                aria-hidden
                className="pointer-events-none absolute top-1/2 left-1/2 block size-2 rounded-[2px]"
                style={{ backgroundColor: colors[i % colors.length] }}
                initial={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 1 }}
                animate={{
                  x: Math.cos(angle) * distance,
                  y: Math.sin(angle) * distance - 20,
                  opacity: 0,
                  rotate: 180 + i * 30,
                  scale: 0.6,
                }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              />
            );
          })
        : null}
    </AnimatePresence>
  );
}

export { ClaimPreview };
