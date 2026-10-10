"use client";

import { useSyncExternalStore } from "react";

import { formatDateTime, formatUtcTime } from "@/lib/time";

const noopSubscribe = () => () => {};

/**
 * A date in the viewer's own time zone. The server doesn't know that zone, so
 * it renders UTC first and the browser swaps in local time after hydration.
 */
function LocalDateTime({ value, className }: { value: string | Date; className?: string }) {
  const inBrowser = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const date = new Date(value);
  return (
    <time dateTime={date.toISOString()} className={className}>
      {inBrowser ? formatDateTime(date) : `${formatDateTime(date, "UTC")} UTC`}
    </time>
  );
}

/** "18:00 UTC", shown next to local times so everyone shares one clock. */
function UtcTime({ value, className }: { value: string | Date; className?: string }) {
  return <span className={className}>{formatUtcTime(value)}</span>;
}

export { LocalDateTime, UtcTime };
