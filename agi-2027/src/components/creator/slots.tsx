"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";

import { cn } from "@/lib/utils";

import { springMove, springPop } from "./motion";

/**
 * A number that rolls to its new value like an odometer: down when it shrinks,
 * up when it grows. Used for slots left, so a claim visibly takes one.
 */
function RollingNumber({ value, className }: { value: number; className?: string }) {
  const [last, setLast] = useState({ value, direction: 0 });
  if (last.value !== value) {
    setLast({ value, direction: value < last.value ? -1 : 1 });
  }
  const direction = last.direction;

  return (
    <span className={cn("relative inline-grid overflow-hidden tabular [&>*]:[grid-area:1/1]", className)}>
      <AnimatePresence initial={false} custom={direction}>
        <motion.span
          key={value}
          custom={direction}
          variants={{
            enter: (d: number) => ({ y: d < 0 ? "-75%" : "75%", opacity: 0 }),
            center: { y: "0%", opacity: 1 },
            exit: (d: number) => ({ y: d < 0 ? "75%" : "-75%", opacity: 0 }),
          }}
          initial="enter"
          animate="center"
          exit="exit"
          transition={springMove}
          className="text-center"
        >
          {value}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

/**
 * How full a campaign is. Small campaigns get one pill per slot, so you can
 * count what's left at a glance; big ones get a bar.
 */
function SlotsMeter({ total, taken, className }: { total: number; taken: number; className?: string }) {
  const left = Math.max(0, total - taken);
  const share = total > 0 ? Math.min(1, taken / total) : 1;
  const low = left > 0 && left / total <= 0.2;
  const label = `${Math.min(taken, total)} of ${total} slots taken`;

  if (total > 0 && total <= 12) {
    return (
      <div role="img" aria-label={label} className={cn("flex h-2 w-full gap-[3px]", className)}>
        {Array.from({ length: total }, (_, index) => {
          const filled = index < taken;
          return (
            <motion.span
              key={index}
              initial={false}
              animate={{ scaleY: filled ? 1 : 0.7, opacity: 1 }}
              transition={springPop}
              data-tone={low && filled ? "orange" : undefined}
              className={cn(
                "h-full flex-1 rounded-full transition-colors duration-300",
                filled ? (left === 0 ? "bg-subtle-foreground/55" : low ? "bg-(--tone-fg)" : "bg-foreground/80") : "bg-surface-3",
              )}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div role="img" aria-label={label} className={cn("h-2 w-full overflow-hidden rounded-full bg-surface-3", className)}>
      <motion.div
        data-tone={low ? "orange" : undefined}
        className={cn(
          "h-full origin-left rounded-full",
          left === 0 ? "bg-subtle-foreground/55" : low ? "bg-(--tone-fg)" : "bg-foreground/80",
        )}
        initial={false}
        animate={{ scaleX: share }}
        transition={springMove}
      />
    </div>
  );
}

export { RollingNumber, SlotsMeter };
