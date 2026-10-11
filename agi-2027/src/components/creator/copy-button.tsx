"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";

import { pressed, springPop } from "./motion";

async function writeClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Older browsers and some embedded views: fall back to a hidden field.
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const ok = document.execCommand("copy");
    field.remove();
    return ok;
  }
}

/** Copies text, then shows a tick for a moment. */
function CopyButton({
  value,
  label = "Copy",
  copiedLabel = "Copied",
  toastMessage,
  iconOnly = false,
  className,
}: {
  value: string;
  label?: string;
  copiedLabel?: string;
  toastMessage?: string;
  iconOnly?: boolean;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  async function copy() {
    const ok = await writeClipboard(value);
    if (!ok) {
      toast.error("Couldn't copy. Select the text and copy it yourself.");
      return;
    }
    setCopied(true);
    if (toastMessage) toast.success(toastMessage);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 1600);
  }

  return (
    <motion.button
      type="button"
      onClick={copy}
      whileTap={pressed}
      aria-label={iconOnly ? `${label}: ${value}` : undefined}
      className={cn(
        "inline-flex h-11 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded-full border border-border-strong bg-surface text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2",
        iconOnly ? "w-11" : "px-3.5",
        className,
      )}
    >
      <span className="relative inline-grid size-4 [&>*]:[grid-area:1/1]">
        <AnimatePresence initial={false}>
          <motion.span
            key={copied ? "done" : "copy"}
            initial={{ scale: 0.4, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.4, opacity: 0 }}
            transition={springPop}
            className="flex items-center justify-center"
          >
            {copied ? <Check className="size-4 text-(--tone-green)" strokeWidth={2.5} /> : <Copy className="size-4" />}
          </motion.span>
        </AnimatePresence>
      </span>
      {iconOnly ? null : <span>{copied ? copiedLabel : label}</span>}
      <span className="sr-only" aria-live="polite">
        {copied ? copiedLabel : ""}
      </span>
    </motion.button>
  );
}

export { CopyButton, writeClipboard };
