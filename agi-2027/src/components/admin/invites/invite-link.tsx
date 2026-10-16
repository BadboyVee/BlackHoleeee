"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { writeClipboard } from "@/components/creator/copy-button";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { springArrive } from "../motion";

/*
 * An invite's address. Links are long, so the start gives way first and the
 * code at the end, the part that tells links apart, always stays in view.
 * Active links sit in a field with a Copy button; the rest show the text
 * only, still selectable.
 */

function LinkText({ link, code, className }: { link: string; code: string; className?: string }) {
  const split = code && link.endsWith(code) ? link.length - code.length : link.length;
  return (
    <span title={link} translate="no" className={cn("flex min-w-0 font-mono text-[13px] leading-5 select-all", className)}>
      <span className="truncate">{link.slice(0, split)}</span>
      <span className="shrink-0">{link.slice(split)}</span>
    </span>
  );
}

export function InviteLinkField({
  link,
  code,
  active,
  describedBy,
}: {
  link: string;
  code: string;
  active: boolean;
  /** Ids of the row's name and date, so "Copy" says which link it copies. */
  describedBy?: string;
}) {
  if (!active) {
    return <LinkText link={link} code={code} className="text-subtle-foreground" />;
  }
  return (
    <div className="flex min-w-0 items-center gap-2">
      <div className="flex h-11 min-w-0 flex-1 items-center rounded-xl border border-input bg-surface-2/50 px-3.5 text-foreground">
        <LinkText link={link} code={code} className="w-full" />
      </div>
      <CopyLinkButton value={link} describedBy={describedBy} />
    </div>
  );
}

/** Copies the link, then shows a tick for a moment. */
function CopyLinkButton({ value, describedBy }: { value: string; describedBy?: string }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  async function copy() {
    const ok = await writeClipboard(value);
    if (!ok) {
      toast.error("Couldn't copy. Select the link and copy it yourself.");
      return;
    }
    setCopied(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 1600);
  }

  return (
    <>
      <Button
        type="button"
        variant="secondary"
        size="lg"
        onClick={copy}
        aria-label="Copy link"
        aria-describedby={describedBy}
        className="min-w-[6.25rem] px-4 text-sm"
      >
        <span className="relative inline-grid size-4 [&>*]:[grid-area:1/1]" aria-hidden>
          <AnimatePresence initial={false}>
            <motion.span
              key={copied ? "done" : "copy"}
              initial={{ scale: 0.4, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.4, opacity: 0 }}
              transition={springArrive}
              className="flex items-center justify-center"
            >
              {copied ? (
                <Check data-tone="green" className="size-4 text-(--tone-fg)" strokeWidth={2.5} />
              ) : (
                <Copy className="size-4" />
              )}
            </motion.span>
          </AnimatePresence>
        </span>
        {copied ? "Copied" : "Copy"}
      </Button>
      <span className="sr-only" aria-live="polite">
        {copied ? "Link copied" : ""}
      </span>
    </>
  );
}
