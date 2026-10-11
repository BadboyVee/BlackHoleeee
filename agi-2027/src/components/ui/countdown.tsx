"use client";

import { useSyncExternalStore } from "react";

import { formatCountdown } from "@/lib/time";
import { cn } from "@/lib/utils";

function subscribe(onTick: () => void) {
  const id = window.setInterval(onTick, 1000);
  return () => window.clearInterval(id);
}

// Stable within a second, so React only re-renders when the text changes.
const getNow = () => Math.floor(Date.now() / 1000) * 1000;
const getServerNow = () => null;

type CountdownProps = {
  to: string | Date;
  className?: string;
  endedLabel?: string;
};

/** Live countdown. Renders a placeholder on the server and ticks in the browser. */
function Countdown({ to, className, endedLabel = "Ended" }: CountdownProps) {
  const now = useSyncExternalStore(subscribe, getNow, getServerNow);
  const target = new Date(to).getTime();

  if (now === null) {
    return (
      <span aria-hidden className={cn("tabular text-subtle-foreground", className)}>
        --
      </span>
    );
  }

  const remaining = target - now;
  return (
    <time dateTime={new Date(target).toISOString()} className={cn("tabular", className)}>
      {remaining > 0 ? formatCountdown(remaining) : endedLabel}
    </time>
  );
}

export { Countdown };
