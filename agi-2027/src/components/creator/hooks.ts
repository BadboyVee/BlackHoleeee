"use client";

import { useCallback, useSyncExternalStore } from "react";

const noopSubscribe = () => () => {};
const isTrue = () => true;
const isFalse = () => false;

/**
 * False on the server and during hydration, true afterwards. Anything that
 * depends on the clock or on this browser's saved demo state renders a
 * placeholder until then, so the server and browser HTML always match.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(noopSubscribe, isTrue, isFalse);
}

/* One shared clock for every countdown on the page. */
const listeners = new Set<() => void>();
let timer: ReturnType<typeof setInterval> | undefined;

function subscribeClock(onTick: () => void) {
  listeners.add(onTick);
  if (timer === undefined) {
    timer = setInterval(() => {
      for (const listener of listeners) listener();
    }, 1000);
  }
  return () => {
    listeners.delete(onTick);
    if (listeners.size === 0 && timer !== undefined) {
      clearInterval(timer);
      timer = undefined;
    }
  };
}

const snapshots = new Map<number, () => number>();
function snapshotFor(stepMs: number) {
  let read = snapshots.get(stepMs);
  if (!read) {
    // Stable within each step, so React re-renders only when the value changes.
    read = () => Math.floor(Date.now() / stepMs) * stepMs;
    snapshots.set(stepMs, read);
  }
  return read;
}
const serverNow = () => null;

/** The current time in ms, rounded down to `stepMs`. Null on the server and while hydrating. */
export function useNow(stepMs = 1000): number | null {
  return useSyncExternalStore(subscribeClock, snapshotFor(stepMs), serverNow);
}

/** Whether a media query matches. False on the server. */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const list = window.matchMedia(query);
      list.addEventListener("change", onChange);
      return () => list.removeEventListener("change", onChange);
    },
    [query],
  );
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches, isFalse);
}
