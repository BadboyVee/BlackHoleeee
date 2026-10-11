"use client";

import { RadioGroup } from "radix-ui";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export type Choice<T extends string> = {
  value: T;
  label: React.ReactNode;
  hint?: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
};

type ChoiceCardsProps<T extends string> = {
  id?: string;
  value: T;
  onChange: (value: T) => void;
  choices: Choice<T>[];
  columns?: 1 | 2 | 3;
  "aria-labelledby"?: string;
  "aria-label"?: string;
  "aria-describedby"?: string;
  invalid?: boolean;
  className?: string;
  /** Forwarded so form libraries can focus the group on an error. */
  ref?: React.Ref<HTMLDivElement>;
};

/**
 * Selectable cards: a radio group where each option explains itself. Arrow
 * keys move between cards, Space picks one.
 */
export function ChoiceCards<T extends string>({
  id,
  value,
  onChange,
  choices,
  columns = 2,
  invalid,
  className,
  ref,
  ...aria
}: ChoiceCardsProps<T>) {
  return (
    <RadioGroup.Root
      ref={ref}
      id={id}
      value={value}
      onValueChange={(next) => onChange(next as T)}
      aria-invalid={invalid || undefined}
      className={cn(
        "grid gap-2.5",
        columns === 2 && "sm:grid-cols-2",
        columns === 3 && "sm:grid-cols-2 lg:grid-cols-3",
        className,
      )}
      {...aria}
    >
      {choices.map((choice) => {
        const selected = choice.value === value;
        return (
          <RadioGroup.Item
            key={choice.value}
            value={choice.value}
            disabled={choice.disabled}
            className={cn(
              "group relative flex min-h-[4.25rem] cursor-pointer items-start gap-3 rounded-lg border bg-surface px-3.5 py-3 text-left outline-none",
              "transition-[border-color,background-color,box-shadow] duration-150",
              "focus-visible:ring-4 focus-visible:ring-ring/20 focus-visible:border-ring",
              "disabled:cursor-not-allowed disabled:opacity-50",
              selected
                ? "border-foreground/70 bg-surface shadow-[0_0_0_1px_var(--foreground)]"
                : "border-border hover:border-border-strong hover:bg-surface-2/40",
            )}
          >
            {choice.icon && columns !== 3 ? (
              <span
                className={cn(
                  "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md border transition-colors",
                  selected ? "border-foreground bg-foreground text-background" : "bg-surface-2 text-muted-foreground",
                )}
              >
                {choice.icon}
              </span>
            ) : null}
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2 text-sm font-medium text-foreground">
                {choice.icon && columns === 3 ? (
                  <span
                    className={cn(
                      "flex size-6 shrink-0 items-center justify-center rounded-md border transition-colors [&_svg]:size-3.5",
                      selected ? "border-foreground bg-foreground text-background" : "bg-surface-2 text-muted-foreground",
                    )}
                  >
                    {choice.icon}
                  </span>
                ) : null}
                {choice.label}
              </span>
              {choice.hint ? (
                <span className={cn("block text-[13px] leading-snug text-muted-foreground", columns === 3 ? "mt-1.5" : "mt-0.5")}>
                  {choice.hint}
                </span>
              ) : null}
            </span>
            <span
              aria-hidden
              className={cn(
                "mt-0.5 flex size-[18px] shrink-0 items-center justify-center rounded-full border transition-colors",
                selected ? "border-foreground bg-foreground text-background" : "border-border-strong",
              )}
            >
              {selected ? <Check className="size-3" strokeWidth={3} /> : null}
            </span>
          </RadioGroup.Item>
        );
      })}
    </RadioGroup.Root>
  );
}
