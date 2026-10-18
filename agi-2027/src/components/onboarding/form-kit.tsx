"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";
import { CircleAlert, CircleCheck } from "lucide-react";

import { SCROLL_MARGIN } from "@/components/auth/parts";
import { fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { COUNTRIES } from "@/lib/creators/countries";
import { MAX_NICHES, NICHES } from "@/lib/creators/options";
import type { CreatorFormState } from "@/lib/creators/schemas";
import { cn } from "@/lib/utils";

/*
 * Pieces the creator forms share: the application, the profile, payout
 * details, invites and reviews. Each form checks its fields in the browser
 * with the shared schema first; the server action has the last word.
 */

export const IDLE: CreatorFormState = { status: "idle" };

/** A titled group of fields. The legend is the fieldset's first child, which is what names the group. */
export function FormSection({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <fieldset className={cn("grid min-w-0 gap-5", className)}>
      <legend className={cn("text-[15px] font-semibold tracking-[-0.01em]", description ? "mb-1" : "mb-5")}>{title}</legend>
      {description ? <p className="text-[13px] leading-snug text-pretty text-muted-foreground">{description}</p> : null}
      {children}
    </fieldset>
  );
}

/** A quiet count that appears near the limit. */
export function CharactersLeft({ value, limit, className }: { value: string; limit: number; className?: string }) {
  const left = limit - value.length;
  if (left > 100) return null;
  return (
    <p
      aria-live="polite"
      className={cn("text-right text-xs tabular-nums", left <= 20 ? "text-destructive-text" : "text-muted-foreground", className)}
    >
      {left === 1 ? "1 character left" : `${left} characters left`}
    </p>
  );
}

/** The "saved" answer under a form's button, read out once. */
export function SavedNote({ state, className }: { state: CreatorFormState; className?: string }) {
  if (state.status !== "saved" || !state.message) return null;
  return (
    <p role="status" data-tone="green" className={cn("flex items-center gap-1.5 text-[13px] text-foreground", className)}>
      <CircleCheck className="size-4 shrink-0 text-(--tone-fg)" aria-hidden />
      {state.message}
    </p>
  );
}

/** A field error outside a <Field>, such as under a group of chips. */
export function GroupError({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <p id={id} role="alert" className="mt-2 flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
      <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
      {message}
    </p>
  );
}

/** Chip look for checkbox and radio pills: 44px tall, the checked one filled. */
export const chipClass = cn(
  "inline-flex h-11 items-center rounded-full border border-border-strong bg-surface px-4 text-[15px] font-medium text-foreground select-none",
  "transition-[background-color,border-color,color,box-shadow,opacity] duration-150 ease-snap",
  "hover:border-foreground/40 hover:bg-surface-2",
  "peer-checked:border-foreground peer-checked:bg-foreground peer-checked:text-background",
  "peer-focus-visible:ring-4 peer-focus-visible:ring-ring/25",
  "peer-disabled:cursor-not-allowed peer-disabled:opacity-45 peer-disabled:hover:bg-surface",
);

/**
 * Niches as checkbox chips, up to MAX_NICHES. Once the limit is reached the
 * rest switch off, so nobody picks six and only learns on submit.
 */
export function NichePicker({
  id,
  selected,
  error,
  register,
  className,
}: {
  id: string;
  selected: readonly string[];
  error?: string;
  register: UseFormRegisterReturn;
  className?: string;
}) {
  const full = selected.length >= MAX_NICHES;
  const hintId = `${id}-hint`;
  return (
    <fieldset
      aria-describedby={error ? `${id}-error` : hintId}
      aria-invalid={error ? true : undefined}
      className={cn("group/niches min-w-0", className)}
    >
      <legend className="mb-1 text-sm leading-none font-medium">What do you post about?</legend>
      <p id={hintId} className="mb-3 text-[13px] text-muted-foreground">
        Pick up to {MAX_NICHES}. {selected.length > 0 ? `${selected.length} picked.` : null}
      </p>
      <div className="flex flex-wrap gap-2">
        {NICHES.map((niche) => {
          const checked = selected.includes(niche.value);
          return (
            <label key={niche.value} className="relative cursor-pointer has-disabled:cursor-not-allowed">
              <input
                type="checkbox"
                value={niche.value}
                // Saved picks show in the server's HTML, before the form library takes over.
                defaultChecked={checked}
                disabled={full && !checked}
                className={cn("peer sr-only", SCROLL_MARGIN)}
                {...register}
              />
              <span className={cn(chipClass, "group-aria-invalid/niches:border-destructive-text")}>{niche.label}</span>
            </label>
          );
        })}
      </div>
      <GroupError id={`${id}-error`} message={error} />
    </fieldset>
  );
}

/** Country as a native select: 250 options are easier in the phone's own picker. */
export function CountrySelect({
  id,
  error,
  hint,
  register,
  defaultValue,
}: {
  id: string;
  error?: string;
  hint?: string;
  register: UseFormRegisterReturn;
  defaultValue?: string;
}) {
  return (
    <NativeSelect
      id={id}
      required
      autoComplete="country"
      // With no default the browser would show, and send, the first country until the page's JavaScript runs.
      defaultValue={defaultValue ?? ""}
      aria-invalid={error ? true : undefined}
      aria-describedby={fieldDescribedBy(id, { hint, error })}
      className={SCROLL_MARGIN}
      {...register}
    >
      <option value="" disabled>
        Pick a country
      </option>
      {COUNTRIES.map((country) => (
        <option key={country.code} value={country.code}>
          {country.name}
        </option>
      ))}
    </NativeSelect>
  );
}

/** A text input with a fixed "@" in front, for X handles. A typed "@" is dropped so it never reads "@@". */
export function HandleInput({
  id,
  error,
  hint,
  register,
  ...props
}: Omit<React.ComponentProps<typeof Input>, "id"> & { id: string; error?: string; hint?: string; register: UseFormRegisterReturn }) {
  return (
    <div className="relative">
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-base text-muted-foreground sm:text-[15px]"
      >
        @
      </span>
      <Input
        id={id}
        type="text"
        autoComplete="off"
        autoCapitalize="none"
        spellCheck={false}
        maxLength={64}
        aria-invalid={error ? true : undefined}
        aria-describedby={fieldDescribedBy(id, { hint, error })}
        {...props}
        {...register}
        className={cn(SCROLL_MARGIN, "pl-8")}
        onChange={(event) => {
          const value = event.target.value;
          if (value.startsWith("@")) event.target.value = value.replace(/^@+/, "");
          return register.onChange(event);
        }}
      />
    </div>
  );
}

/**
 * Brings a form's success into view and gives it focus once, so it's seen
 * and read out. Returns the ref for the heading. Pass false to skip it.
 */
export function useFocusOnMount<T extends HTMLElement>(enabled = true) {
  const ref = useRef<T>(null);
  useEffect(() => {
    const element = ref.current;
    if (!enabled || !element) return;
    element.focus({ preventScroll: true });
    element.scrollIntoView({ block: "center" });
  }, [enabled]);
  return ref;
}

const noopSubscribe = () => () => {};

/**
 * Wraps what the server shows in place of a form it has just answered, such
 * as the application's status once it's sent. Arriving like that, it takes
 * focus; on a fresh page load it leaves focus where the browser put it.
 */
export function FocusOnArrival({ children, className }: { children: React.ReactNode; className?: string }) {
  // False while the server's HTML hydrates, true when this first renders in the browser.
  const inBrowser = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const [arrived] = useState(inBrowser);
  const ref = useFocusOnMount<HTMLDivElement>(arrived);
  return (
    <div ref={ref} tabIndex={-1} className={cn("outline-none", className)}>
      {children}
    </div>
  );
}
