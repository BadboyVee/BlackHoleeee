"use client";

import { useId } from "react";
import { motion } from "motion/react";
import { RadioGroup } from "radix-ui";

import { cn } from "@/lib/utils";
import { springMove } from "./motion";

export type SegmentedOption<T extends string> = {
  value: T;
  label: React.ReactNode;
  icon?: React.ReactNode;
  /** Accessible name when the label is an icon or abbreviated. */
  ariaLabel?: string;
};

type SegmentedProps<T extends string> = {
  value: T;
  onChange: (value: T) => void;
  options: SegmentedOption<T>[];
  "aria-label"?: string;
  "aria-labelledby"?: string;
  size?: "sm" | "md";
  /** Stretch the options to fill the width. */
  block?: boolean;
  className?: string;
  id?: string;
};

/**
 * A segmented control: a radio group that looks like a row of pills. Arrow
 * keys move between options; the highlight slides to the chosen one.
 */
function Segmented<T extends string>({
  value,
  onChange,
  options,
  size = "md",
  block = false,
  className,
  id,
  ...aria
}: SegmentedProps<T>) {
  const layoutId = useId();
  return (
    <RadioGroup.Root
      id={id}
      value={value}
      onValueChange={(next) => onChange(next as T)}
      orientation="horizontal"
      loop
      className={cn(
        "relative inline-flex max-w-full items-center gap-0.5 overflow-x-auto rounded-full border bg-surface-2/70 p-0.5 [scrollbar-width:none]",
        block && "flex w-full",
        className,
      )}
      {...aria}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <RadioGroup.Item
            key={option.value}
            value={option.value}
            aria-label={option.ariaLabel}
            className={cn(
              "relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded-full font-medium whitespace-nowrap transition-colors duration-150 outline-none",
              "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring",
              size === "sm" ? "h-8 px-3 text-[13px] pointer-coarse:h-10" : "h-10 px-4 text-sm",
              block && "flex-1",
              active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {active ? (
              <motion.span
                layoutId={layoutId}
                transition={springMove}
                aria-hidden
                className="absolute inset-0 rounded-full border border-border-strong bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.1)]"
              />
            ) : null}
            {option.icon ? <span className="relative flex items-center">{option.icon}</span> : null}
            <span className="relative">{option.label}</span>
          </RadioGroup.Item>
        );
      })}
    </RadioGroup.Root>
  );
}

export { Segmented };
