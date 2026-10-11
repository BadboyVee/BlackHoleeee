"use client";

import { Children, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { cn } from "@/lib/utils";

import { pressed, springArrive } from "./motion";

/**
 * A horizontal row that snaps card by card: swipe on phones, arrows on bigger
 * screens. The arrows hide at either end, watched with an observer.
 */
function Carousel({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  const scroller = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ start: true, end: true });
  const reduce = useReducedMotion();
  const count = Children.count(children);

  useEffect(() => {
    const root = scroller.current;
    if (!root || root.children.length === 0) return;
    const first = root.children[0];
    const last = root.children[root.children.length - 1];
    const observer = new IntersectionObserver(
      (entries) => {
        setEdges((previous) => {
          const next = { ...previous };
          for (const entry of entries) {
            const visible = entry.intersectionRatio > 0.92;
            if (entry.target === first) next.start = visible;
            if (entry.target === last) next.end = visible;
          }
          return next.start === previous.start && next.end === previous.end ? previous : next;
        });
      },
      { root, threshold: [0, 0.5, 0.92, 1] },
    );
    observer.observe(first);
    observer.observe(last);
    return () => observer.disconnect();
  }, [count]);

  function scrollBy(direction: 1 | -1) {
    const root = scroller.current;
    const card = root?.children[0];
    if (!root || !card) return;
    const step = card.getBoundingClientRect().width + 12;
    root.scrollBy({ left: direction * step, behavior: reduce ? "auto" : "smooth" });
  }

  return (
    <div className={cn("group/carousel relative", className)}>
      <div
        ref={scroller}
        role="list"
        aria-label={label}
        className={cn(
          "-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto overscroll-x-contain scroll-smooth px-4 pt-2 pb-5 [scrollbar-width:none] motion-reduce:scroll-auto [&::-webkit-scrollbar]:hidden",
          "scroll-px-4 sm:-mx-6 sm:scroll-px-6 sm:px-6 lg:-mx-10 lg:scroll-px-10 lg:px-10",
        )}
      >
        {children}
      </div>
      <AnimatePresence>
        {[
          { direction: -1 as const, show: !edges.start, side: "left-0 -translate-x-1/3", icon: ChevronLeft, label: "Previous" },
          { direction: 1 as const, show: !edges.end, side: "right-0 translate-x-1/3", icon: ChevronRight, label: "Next" },
        ]
          .filter((control) => control.show)
          .map(({ direction, side, icon: Icon, label: text }) => (
            <motion.button
              key={direction}
              type="button"
              onClick={() => scrollBy(direction)}
              aria-label={`${text} campaigns`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              whileTap={pressed}
              transition={springArrive}
              className={cn(
                "absolute top-[42%] z-20 hidden size-11 cursor-pointer items-center justify-center rounded-full border border-border-strong bg-popover/95 text-foreground shadow-float backdrop-blur-md hover:bg-surface-2 sm:flex",
                side,
              )}
            >
              <Icon className="size-5" />
            </motion.button>
          ))}
      </AnimatePresence>
    </div>
  );
}

function CarouselItem({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div role="listitem" className={cn("w-[86%] max-w-[22rem] shrink-0 snap-start sm:w-[21.5rem] xl:w-[calc((100%-1.5rem)/3)]", className)}>
      {children}
    </div>
  );
}

export { Carousel, CarouselItem };
