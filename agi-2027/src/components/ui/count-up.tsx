"use client";

import { useEffect, useRef } from "react";

import { formatXCount, withCommas } from "@/lib/creators/display";
import { cn } from "@/lib/utils";

type CountFormat = "compact" | "plain";

/**
 * The number as text. No Intl: ICU versions differ between Node and browsers,
 * which breaks hydration, so the server and every browser write the same.
 * compact reads the way X shows counts (9,560, then 128.6K), rounding down so
 * a number never reads higher than it is; plain is a whole number with
 * commas (12,400).
 */
export function countText(value: number, format: CountFormat): string {
  return format === "compact" ? formatXCount(value) : withCommas(value);
}

type CountUpProps = {
  value: number;
  /** compact: 9,560 or 12.4M, the way X shows counts. plain: 12,400,000. */
  format?: CountFormat;
  prefix?: string;
  suffix?: string;
  durationMs?: number;
  className?: string;
};

/**
 * Counts up from zero the first time it scrolls into view. The server renders
 * the final number, so it reads correctly without JavaScript and for screen
 * readers; numbers already on screen at load stay put instead of flashing.
 */
function CountUp({
  value,
  format = "compact",
  prefix = "",
  suffix = "",
  durationMs = 1600,
  className,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const finalText = `${prefix}${countText(value, format)}${suffix}`;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) return;

    let frame = 0;
    el.textContent = `${prefix}${countText(0, format)}${suffix}`;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const t = Math.min(1, (now - start) / durationMs);
          const eased = 1 - Math.pow(1 - t, 4);
          el.textContent = `${prefix}${countText(value * eased, format)}${suffix}`;
          if (t < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
      },
      { threshold: 0.35 },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
      el.textContent = finalText;
    };
  }, [value, prefix, suffix, durationMs, format, finalText]);

  return (
    <span className={cn("tabular", className)}>
      <span ref={ref} aria-hidden>
        {finalText}
      </span>
      <span className="sr-only">{finalText}</span>
    </span>
  );
}

export { CountUp };
