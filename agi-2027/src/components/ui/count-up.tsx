"use client";

import { useEffect, useMemo, useRef } from "react";

import { cn } from "@/lib/utils";

type CountUpProps = {
  value: number;
  /** compact: 12.4M. plain: 12,400,000. */
  format?: "compact" | "plain";
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
  const formatter = useMemo(
    () =>
      new Intl.NumberFormat(
        "en-US",
        format === "compact"
          ? { notation: "compact", maximumFractionDigits: 1 }
          : { maximumFractionDigits: 0 },
      ),
    [format],
  );
  const finalText = `${prefix}${formatter.format(value)}${suffix}`;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) return;

    let frame = 0;
    el.textContent = `${prefix}${formatter.format(0)}${suffix}`;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const t = Math.min(1, (now - start) / durationMs);
          const eased = 1 - Math.pow(1 - t, 4);
          el.textContent = `${prefix}${formatter.format(value * eased)}${suffix}`;
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
  }, [value, prefix, suffix, durationMs, formatter, finalText]);

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
