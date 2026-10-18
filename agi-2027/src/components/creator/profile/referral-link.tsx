"use client";

import { useId, useSyncExternalStore } from "react";
import { Share2 } from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";

import { CopyButton } from "../copy-button";
import { pressed } from "../motion";

const noopSubscribe = () => () => {};
const canShareHere = () => typeof navigator.share === "function";
const notOnServer = () => false;

/** The share sheet on phones (and some desktops). Hidden until hydrated, and where there's none. */
function ShareButton({ link }: { link: string }) {
  const canShare = useSyncExternalStore(noopSubscribe, canShareHere, notOnServer);
  if (!canShare) return null;

  async function share() {
    try {
      await navigator.share({ title: "Apply to AGI 2027", url: link });
    } catch (error) {
      // Closing the share sheet isn't a failure.
      if (error instanceof DOMException && error.name === "AbortError") return;
      toast.error("Couldn't open sharing. Copy the link instead.");
    }
  }

  return (
    <motion.button
      type="button"
      onClick={share}
      whileTap={pressed}
      className="inline-flex h-11 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded-full border border-border-strong bg-surface px-3.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2"
    >
      <Share2 className="size-4" aria-hidden />
      Share
    </motion.button>
  );
}

function Count({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col-reverse gap-1.5 rounded-xl border bg-surface-2/50 px-4 py-3.5">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="text-figure text-[1.75rem] leading-none">{value}</dd>
    </div>
  );
}

/**
 * The creator's personal link to /apply. Copy it or share it; every
 * application that comes through it shows who sent them.
 */
export function ReferralLink({
  link,
  counts,
}: {
  link: string;
  /** How many applied through the link, and how many of those were approved. Null when it couldn't be read. */
  counts: { applied: number; approved: number } | null;
}) {
  const fieldId = useId();
  return (
    <div className="grid gap-5">
      <div className="grid gap-2">
        <label htmlFor={fieldId} className="text-sm leading-none font-medium">
          Your link
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            id={fieldId}
            type="text"
            readOnly
            value={link}
            spellCheck={false}
            onFocus={(event) => event.currentTarget.select()}
            className="font-mono"
          />
          <div className="flex gap-2 [&>*]:flex-1 sm:[&>*]:flex-none">
            <CopyButton value={link} label="Copy link" copiedLabel="Copied" toastMessage="Link copied" />
            <ShareButton link={link} />
          </div>
        </div>
      </div>

      {counts ? (
        <dl className="grid grid-cols-2 gap-3 sm:max-w-sm">
          <Count value={counts.applied} label="Applied" />
          <Count value={counts.approved} label="Approved" />
        </dl>
      ) : null}

      <p className="text-sm text-pretty text-muted-foreground">Know a creator who&apos;d fit? Their application shows you sent them.</p>
    </div>
  );
}
