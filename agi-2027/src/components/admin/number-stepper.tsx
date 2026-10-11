"use client";

import { Minus, Plus } from "lucide-react";

import { cn } from "@/lib/utils";

type NumberStepperProps = {
  id: string;
  value: number;
  onChange: (value: number) => void;
  onBlur?: () => void;
  min?: number;
  max?: number;
  step?: number;
  invalid?: boolean;
  "aria-describedby"?: string;
  inputRef?: (node: HTMLInputElement | null) => void;
  className?: string;
};

/** A number with big minus and plus buttons. Arrow keys work in the field too. */
export function NumberStepper({
  id,
  value,
  onChange,
  onBlur,
  min = 1,
  max = 1000,
  step = 1,
  invalid,
  inputRef,
  className,
  ...aria
}: NumberStepperProps) {
  const safe = Number.isFinite(value) ? value : min;
  const set = (next: number) => onChange(Math.min(max, Math.max(min, next)));
  return (
    <div
      className={cn(
        "inline-flex h-11 items-stretch overflow-hidden rounded-xl border border-input bg-surface shadow-xs transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-4 focus-within:ring-ring/20",
        invalid && "border-destructive-text",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => set(safe - step)}
        disabled={safe <= min}
        aria-label="One fewer"
        className="flex w-11 cursor-pointer items-center justify-center text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground disabled:cursor-default disabled:opacity-35 disabled:hover:bg-transparent"
      >
        <Minus className="size-4" />
      </button>
      <input
        ref={inputRef}
        id={id}
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        step={step}
        value={Number.isFinite(value) ? value : ""}
        onChange={(event) => onChange(event.target.value === "" ? Number.NaN : Number(event.target.value))}
        onBlur={onBlur}
        aria-invalid={invalid || undefined}
        className="w-16 border-x border-input bg-transparent text-center text-base font-medium tabular outline-none [appearance:textfield] sm:text-[15px] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        {...aria}
      />
      <button
        type="button"
        onClick={() => set(safe + step)}
        disabled={safe >= max}
        aria-label="One more"
        className="flex w-11 cursor-pointer items-center justify-center text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground disabled:cursor-default disabled:opacity-35 disabled:hover:bg-transparent"
      >
        <Plus className="size-4" />
      </button>
    </div>
  );
}
