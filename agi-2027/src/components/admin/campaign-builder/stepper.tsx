"use client";

import { motion } from "motion/react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import { springMove } from "../motion";
import { STEPS } from "./form-values";

/**
 * Six segments that fill as the owner moves through the builder. Any step
 * already reached can be reopened; a red segment marks a step with problems.
 */
export function Stepper({
  step,
  furthest,
  problems,
  onSelect,
}: {
  step: number;
  furthest: number;
  problems: number[];
  onSelect: (index: number) => void;
}) {
  return (
    <nav aria-label="Campaign steps">
      <ol className="grid grid-cols-6 gap-1.5 sm:gap-2">
        {STEPS.map((entry, index) => {
          const current = index === step;
          const done = index < step;
          const reachable = index <= furthest;
          const problem = problems.includes(index);
          return (
            <li key={entry.id} className="min-w-0">
              <button
                type="button"
                onClick={() => onSelect(index)}
                disabled={!reachable}
                aria-current={current ? "step" : undefined}
                aria-label={`Step ${index + 1}, ${entry.title}${done ? ", done" : ""}${problem ? ", needs attention" : ""}`}
                className="group flex min-h-11 w-full min-w-0 cursor-pointer flex-col justify-center gap-2 rounded-md text-left outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-default sm:min-h-0 sm:py-1.5"
              >
                <span className="hidden min-w-0 items-center gap-1.5 text-xs sm:flex">
                  <span className={cn("font-mono text-[11px] tabular", current ? "text-foreground" : "text-subtle-foreground")}>
                    {index + 1}
                  </span>
                  <span
                    className={cn(
                      "truncate font-medium transition-colors",
                      current ? "text-foreground" : reachable ? "text-muted-foreground group-hover:text-foreground" : "text-subtle-foreground",
                    )}
                  >
                    {entry.short}
                  </span>
                  {problem ? (
                    <span aria-hidden className="size-1.5 shrink-0 rounded-full bg-destructive-text" />
                  ) : done ? (
                    <Check aria-hidden className="size-3 shrink-0 text-muted-foreground" strokeWidth={2.5} />
                  ) : null}
                </span>
                <span className="relative block h-1 overflow-hidden rounded-full bg-surface-3">
                  <motion.span
                    aria-hidden
                    className={cn("absolute inset-0 origin-left rounded-full", problem ? "bg-destructive-text" : "bg-foreground")}
                    initial={false}
                    animate={{ scaleX: index <= step ? 1 : 0, opacity: index < step ? 0.55 : 1 }}
                    transition={springMove}
                  />
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
