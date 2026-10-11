"use client";

import { formatCountdown, formatDateTime, formatTime } from "@/lib/time";
import { cn } from "@/lib/utils";

import { useHydrated, useNow } from "./hooks";

const HOUR = 3_600_000;
const DAY = 24 * HOUR;

const dayOf = (formatted: string) => formatted.slice(0, formatted.lastIndexOf(","));
const weekdayOf = (formatted: string) => formatted.slice(0, formatted.indexOf(" "));
const WEEK = 6 * DAY;

/**
 * "Tue 3 Nov, 17:00 to 21:00". A window that runs into another day names the
 * end by weekday ("Sat 7 Nov, 14:00 to Sun 14:00") so it fits on a phone.
 */
export function formatWindow(start: string, end: string, timeZone?: string): string {
  const from = formatDateTime(start, timeZone);
  const to = formatDateTime(end, timeZone);
  if (dayOf(from) === dayOf(to)) return `${from} to ${formatTime(end, timeZone)}`;
  if (new Date(end).getTime() - new Date(start).getTime() < WEEK) {
    return `${from} to ${weekdayOf(to)} ${formatTime(end, timeZone)}`;
  }
  return `${from} to ${to}`;
}

/** "16:00 to 20:00 UTC", the shared clock shown under local times. */
export function formatUtcWindow(start: string, end: string): string {
  const from = formatDateTime(start, "UTC");
  const to = formatDateTime(end, "UTC");
  if (dayOf(from) === dayOf(to)) return `${formatTime(start, "UTC")} to ${formatTime(end, "UTC")} UTC`;
  if (new Date(end).getTime() - new Date(start).getTime() < WEEK) {
    return `${weekdayOf(from)} ${formatTime(start, "UTC")} to ${weekdayOf(to)} ${formatTime(end, "UTC")} UTC`;
  }
  return `${from} to ${to} UTC`;
}

/** A window in the viewer's own time zone. The server shows UTC until the browser takes over. */
export function LocalWindow({ start, end, className }: { start: string; end: string; className?: string }) {
  const inBrowser = useHydrated();
  return (
    <span className={className}>{inBrowser ? formatWindow(start, end) : `${formatWindow(start, end, "UTC")} UTC`}</span>
  );
}

/** One moment in the viewer's time zone (UTC on the server). */
export function LocalWhen({ value, className }: { value: string; className?: string }) {
  const inBrowser = useHydrated();
  return (
    <time dateTime={new Date(value).toISOString()} className={className}>
      {inBrowser ? formatDateTime(value) : `${formatDateTime(value, "UTC")} UTC`}
    </time>
  );
}

export function urgencyTone(remainingMs: number): "red" | "amber" | "gray" | undefined {
  if (remainingMs <= 0) return "gray";
  if (remainingMs <= HOUR) return "red";
  if (remainingMs <= DAY) return "amber";
  return undefined;
}

/**
 * A live countdown that warms up as time runs out: amber inside a day, red
 * inside an hour. Shows a quiet placeholder until the browser knows the time.
 */
export function TimeLeft({
  to,
  prefix,
  endedLabel = "Ended",
  className,
  calm = false,
}: {
  to: string;
  prefix?: string;
  endedLabel?: string;
  className?: string;
  /** Never change color. */
  calm?: boolean;
}) {
  const now = useNow();
  if (now === null) {
    return (
      <span aria-hidden className={cn("tabular text-subtle-foreground", className)}>
        {prefix ? `${prefix} ` : ""}--
      </span>
    );
  }
  const remaining = new Date(to).getTime() - now;
  const tone = calm ? undefined : urgencyTone(remaining);
  return (
    <time
      dateTime={new Date(to).toISOString()}
      data-tone={tone}
      className={cn("tabular", tone && "text-(--tone-fg)", className)}
    >
      {remaining > 0 ? `${prefix ? `${prefix} ` : ""}${formatCountdown(remaining)}` : endedLabel}
    </time>
  );
}

/** "Just now", "5m ago", "3h ago", or the date for anything older than a day. */
export function Ago({ value, className }: { value: string; className?: string }) {
  const now = useNow(30_000);
  if (now === null) return <span className={className}>&nbsp;</span>;
  const diff = now - new Date(value).getTime();
  let text: string;
  if (diff < 0) text = formatDateTime(value);
  else if (diff < 60_000) text = "Just now";
  else if (diff < HOUR) text = `${Math.floor(diff / 60_000)}m ago`;
  else if (diff < DAY) text = `${Math.floor(diff / HOUR)}h ago`;
  else text = formatDateTime(value);
  return (
    <time dateTime={new Date(value).toISOString()} className={className}>
      {text}
    </time>
  );
}
