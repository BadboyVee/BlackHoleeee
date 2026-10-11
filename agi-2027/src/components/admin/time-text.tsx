"use client";

import { useSyncExternalStore } from "react";

import { formatDateTime, formatTime } from "@/lib/time";

/*
 * Local-time text for the owner screens, built on src/lib/time.ts. The server
 * can't know the viewer's time zone, so it renders UTC and the browser swaps
 * in local time after hydration (the same pattern as ui/local-time.tsx).
 * Ranges read "Tue 3 Nov, 16:00 to 20:00".
 */

const noopSubscribe = () => () => {};

/** False on the server and during hydration, true once running in the browser. */
export function useInBrowser() {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}

function dayOf(iso: string, timeZone?: string) {
  return formatDateTime(iso, timeZone).split(",")[0];
}

/** "Tue 3 Nov, 16:00 to 20:00", or both dates when the window spans days. */
export function windowText(start: string, end: string, timeZone?: string) {
  const to = dayOf(start, timeZone) === dayOf(end, timeZone) ? formatTime(end, timeZone) : formatDateTime(end, timeZone);
  return `${formatDateTime(start, timeZone)} to ${to}`;
}

/** "Tue 3 Nov, 16:00 UTC". Safe to render anywhere: it doesn't depend on the viewer. */
export function utcText(iso: string) {
  return `${formatDateTime(iso, "UTC")} UTC`;
}

/** "16:00 to 20:00 UTC", with dates when the window spans days in UTC. */
export function utcWindowText(start: string, end: string) {
  return `${windowText(start, end, "UTC")} UTC`;
}

export function LocalWindow({ start, end, className }: { start: string; end: string; className?: string }) {
  const inBrowser = useInBrowser();
  return (
    <span className={className}>
      {inBrowser ? windowText(start, end) : utcWindowText(start, end)}
    </span>
  );
}

export function LocalWhen({ value, className }: { value: string; className?: string }) {
  const inBrowser = useInBrowser();
  return (
    <time dateTime={value} className={className}>
      {inBrowser ? formatDateTime(value) : utcText(value)}
    </time>
  );
}

/** The time part only, in local time: "16:30". */
export function LocalClock({ value, className }: { value: string; className?: string }) {
  const inBrowser = useInBrowser();
  return (
    <time dateTime={value} className={className}>
      {inBrowser ? formatTime(value) : `${formatTime(value, "UTC")} UTC`}
    </time>
  );
}

/** The viewer's time zone name, e.g. "Europe/London", once in the browser. */
export function useTimeZoneName() {
  const inBrowser = useInBrowser();
  if (!inBrowser) return null;
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone ?? null;
  } catch {
    return null;
  }
}

function subscribeMinute(onTick: () => void) {
  const id = window.setInterval(onTick, 30_000);
  return () => window.clearInterval(id);
}
// Stable within a minute, so React only re-renders when the minute changes.
const getMinute = () => Math.floor(Date.now() / 60_000) * 60_000;
const getServerMinute = () => null;

/** The current time, to the minute. Null on the server and during hydration. */
export function useNowMinute() {
  return useSyncExternalStore(subscribeMinute, getMinute, getServerMinute);
}
