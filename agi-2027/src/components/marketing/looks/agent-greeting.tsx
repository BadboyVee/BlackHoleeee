"use client";

import { useEffect } from "react";
import Link from "next/link";

import { useLook } from "@/components/theme/look-picker";
import { cn } from "@/lib/utils";

type Pill = { href: string; label: string; outline?: boolean };

function tellEcho(mood: "talk" | "curious" | "happy", ms?: number) {
  window.dispatchEvent(new CustomEvent("agi:echo", { detail: { mood, ms } }));
}

/** Echo talks while the greeting streams in. */
function EchoTalks({ ms }: { ms: number }) {
  const look = useLook();
  useEffect(() => {
    if (look !== "agent") return;
    // Echo loads a moment after the page; start talking once it's likely there.
    const timer = window.setTimeout(() => tellEcho("talk", ms), 600);
    return () => window.clearTimeout(timer);
  }, [look, ms]);
  return null;
}

/** The answer buttons. Echo looks up, curious, when one is hovered. */
function GreetingPills({ pills, startMs }: { pills: Pill[]; startMs: number }) {
  return (
    <ul className="mt-7 flex max-w-[34rem] flex-wrap gap-2">
      {pills.map((pill, i) => (
        <li key={pill.label} className="animate-pop" style={{ animationDelay: `${startMs + i * 70}ms` }}>
          <Link
            href={pill.href}
            onPointerEnter={() => tellEcho("curious", 1400)}
            onFocus={() => tellEcho("curious", 1400)}
            onClick={() => tellEcho("happy", 1200)}
            className={cn(
              "pressable inline-flex h-11 items-center rounded-full px-4 text-[14px] font-medium tracking-[-0.01em] transition-colors duration-200 ease-snap sm:h-10 sm:text-[13.5px]",
              pill.outline
                ? "text-white ring-1 ring-white/80 ring-inset hover:bg-white hover:text-[#1a1412]"
                : "bg-white text-[#1a1412] hover:bg-[#1a1412] hover:text-white",
            )}
          >
            {pill.label}
          </Link>
        </li>
      ))}
    </ul>
  );
}

export { EchoTalks, GreetingPills };
export type { Pill };
