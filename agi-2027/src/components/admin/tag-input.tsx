"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { CircleAlert, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { springArrive } from "./motion";

export type TagParser = (raw: string) => { ok: true; value: string } | { ok: false; error: string };

type TagInputProps = {
  id: string;
  value: string[];
  onChange: (next: string[]) => void;
  onBlur?: () => void;
  /** Validates and normalises one tag, e.g. adds the @ to a handle. */
  parse: TagParser;
  placeholder?: string;
  max?: number;
  invalid?: boolean;
  "aria-describedby"?: string;
  /** Forwarded so form libraries can focus the input on an error. */
  inputRef?: (node: HTMLInputElement | null) => void;
};

/**
 * Chips with an inline input. Enter or a comma adds what's typed, pasting a
 * list adds each item, Backspace on an empty input removes the last chip.
 * Each tag is checked before it's added, and duplicates are skipped.
 */
export function TagInput({
  id,
  value,
  onChange,
  onBlur,
  parse,
  placeholder,
  max = 10,
  invalid,
  inputRef,
  ...aria
}: TagInputProps) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const localRef = useRef<HTMLInputElement | null>(null);

  function add(raw: string[]) {
    const next = [...value];
    let problem: string | null = null;
    for (const item of raw.map((entry) => entry.trim()).filter(Boolean)) {
      if (next.length >= max) {
        problem = `Up to ${max}. Remove one to add another.`;
        break;
      }
      const parsed = parse(item);
      if (!parsed.ok) {
        problem = `${item}: ${parsed.error}`;
        continue;
      }
      if (next.some((tag) => tag.toLowerCase() === parsed.value.toLowerCase())) {
        problem = `${parsed.value} is already added.`;
        continue;
      }
      next.push(parsed.value);
    }
    if (next.length !== value.length) onChange(next);
    setError(problem);
    return problem === null;
  }

  function commitDraft() {
    if (!draft.trim()) return true;
    const ok = add(draft.split(/[,\n]/));
    if (ok) setDraft("");
    return ok;
  }

  function remove(index: number) {
    onChange(value.filter((_, i) => i !== index));
    setError(null);
    localRef.current?.focus();
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      commitDraft();
    } else if (event.key === "Backspace" && draft === "" && value.length > 0) {
      event.preventDefault();
      onChange(value.slice(0, -1));
    } else if (event.key === "Escape" && draft) {
      event.preventDefault();
      setDraft("");
      setError(null);
    }
  }

  function onPaste(event: React.ClipboardEvent<HTMLInputElement>) {
    const text = event.clipboardData.getData("text");
    if (!/[,\n]/.test(text)) return;
    event.preventDefault();
    add(text.split(/[,\n]/));
  }

  const full = value.length >= max;
  const describedBy = [aria["aria-describedby"], error ? `${id}-tag-error` : null].filter(Boolean).join(" ") || undefined;

  return (
    <div className="grid gap-1.5">
      <div
        onClick={() => localRef.current?.focus()}
        className={cn(
          "flex min-h-11 w-full cursor-text flex-wrap items-center gap-1.5 rounded-xl border border-input bg-surface px-2 py-1.5 shadow-xs transition-[border-color,box-shadow] duration-150",
          "hover:border-border-strong focus-within:border-ring focus-within:ring-4 focus-within:ring-ring/20",
          (invalid || error) && "border-destructive-text focus-within:ring-destructive-text/20",
        )}
      >
        <ul className="contents" aria-label="Added">
          <AnimatePresence initial={false}>
            {value.map((tag, index) => (
              <motion.li
                key={tag}
                layout
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85, transition: { duration: 0.1 } }}
                transition={springArrive}
                className="inline-flex h-7 items-center gap-1 rounded-full border border-border-strong bg-surface-2 pr-0.5 pl-2.5 text-[13px] font-medium"
              >
                {tag}
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    remove(index);
                  }}
                  className="flex size-6 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
                  aria-label={`Remove ${tag}`}
                >
                  <X className="size-3.5" />
                </button>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
        <input
          ref={(node) => {
            localRef.current = node;
            inputRef?.(node);
          }}
          id={id}
          value={draft}
          disabled={full}
          onChange={(event) => {
            setDraft(event.target.value);
            if (error) setError(null);
          }}
          onKeyDown={onKeyDown}
          onPaste={onPaste}
          onBlur={() => {
            commitDraft();
            onBlur?.();
          }}
          placeholder={full ? `That's the limit of ${max}` : value.length ? "Add another" : placeholder}
          aria-invalid={invalid || Boolean(error) || undefined}
          aria-describedby={describedBy}
          enterKeyHint="done"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          className="h-8 min-w-[8rem] flex-1 bg-transparent px-1.5 text-base outline-none placeholder:text-subtle-foreground disabled:cursor-not-allowed sm:text-[15px]"
        />
      </div>
      {error ? (
        <p id={`${id}-tag-error`} role="alert" className="flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : null}
    </div>
  );
}
