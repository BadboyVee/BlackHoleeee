"use client";

import { motion } from "motion/react";

import { formatDateTime } from "@/lib/time";
import { cn } from "@/lib/utils";
import { springMove } from "./motion";
import { useInBrowser } from "./time-text";

type TimelineInput = {
  /** When it drops. "now" for publish now, empty while unknown. */
  drop: string | "now" | "";
  claimDeadline: string;
  postWindowStart: string;
  postWindowEnd: string;
  proofDeadline: string;
  /** The current time, for "now". */
  now?: number | null;
};

type Point = { key: "drop" | "claim" | "start" | "end" | "proof"; label: string; at: number; problem: boolean };

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "2 days 3 hours", "4 hours", "45 minutes". */
export function humanDuration(ms: number) {
  if (ms < MINUTE) return "less than a minute";
  const days = Math.floor(ms / DAY);
  const hours = Math.floor((ms % DAY) / HOUR);
  const minutes = Math.floor((ms % HOUR) / MINUTE);
  const part = (value: number, unit: string) => `${value} ${unit}${value === 1 ? "" : "s"}`;
  if (days > 0) return hours ? `${part(days, "day")} ${part(hours, "hour")}` : part(days, "day");
  if (hours > 0) return minutes ? `${part(hours, "hour")} ${part(minutes, "minute")}` : part(hours, "hour");
  return part(minutes, "minute");
}

function time(iso: string) {
  if (!iso) return Number.NaN;
  return new Date(iso).getTime();
}

/** Positions in proportion to time, but never closer than minGap, so labels stay readable. */
function layout(points: Point[], minGap = 0.16) {
  const min = points[0].at;
  const span = points[points.length - 1].at - min || 1;
  const positions = points.map((point) => (point.at - min) / span);
  for (let i = 1; i < positions.length; i++) positions[i] = Math.max(positions[i], positions[i - 1] + minGap);
  const last = positions[positions.length - 1];
  return positions.map((position) => (last > 1 ? position / last : position));
}

/**
 * Drop, claim deadline, post window and proof deadline on one line, in the
 * viewer's time. It redraws as times change, and flags anything out of order.
 */
export function CampaignTimeline({ drop, claimDeadline, postWindowStart, postWindowEnd, proofDeadline, now }: TimelineInput) {
  const inBrowser = useInBrowser();
  const dropAt = drop === "now" ? (now ?? Number.NaN) : time(drop);
  const t = {
    claim: time(claimDeadline),
    start: time(postWindowStart),
    end: time(postWindowEnd),
    proof: time(proofDeadline),
  };
  const points: Point[] = (
    [
      { key: "drop", label: drop === "now" ? "Drops now" : "Drops", at: dropAt, problem: dropAt >= t.claim },
      { key: "claim", label: "Claiming closes", at: t.claim, problem: t.claim > t.end },
      { key: "start", label: "Window opens", at: t.start, problem: false },
      { key: "end", label: "Window closes", at: t.end, problem: t.end <= t.start },
      { key: "proof", label: "Proof due", at: t.proof, problem: t.proof < t.end },
    ] satisfies Point[]
  )
    .filter((point) => Number.isFinite(point.at))
    .sort((a, b) => a.at - b.at);

  if (points.length < 2) {
    return (
      <div className="flex h-24 items-center justify-center rounded-lg border border-dashed px-4 text-center text-[13px] text-muted-foreground">
        Set the times and the timeline draws itself here.
      </div>
    );
  }

  const positions = layout(points);
  const left = (key: Point["key"]) => {
    const index = points.findIndex((point) => point.key === key);
    return index === -1 ? null : 4 + positions[index] * 92;
  };
  const bandStart = left("start");
  const bandEnd = left("end");

  const sentences: string[] = [];
  if (Number.isFinite(dropAt) && Number.isFinite(t.claim) && t.claim > dropAt) {
    sentences.push(`${humanDuration(t.claim - dropAt)} to claim`);
  }
  if (Number.isFinite(t.start) && Number.isFinite(t.end) && t.end > t.start) {
    sentences.push(`${humanDuration(t.end - t.start)} to post`);
  }
  if (Number.isFinite(t.end) && Number.isFinite(t.proof) && t.proof >= t.end) {
    sentences.push(`${humanDuration(t.proof - t.end)} after the window to send proof`);
  }
  const problems = points.filter((point) => point.problem);

  return (
    <figure className="grid gap-3">
      <div className="relative h-[7.5rem] select-none" aria-hidden>
        <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-border-strong" />
        {bandStart !== null && bandEnd !== null && bandEnd > bandStart ? (
          <motion.div
            initial={false}
            animate={{ left: `${bandStart}%`, width: `${bandEnd - bandStart}%` }}
            transition={springMove}
            className="absolute top-1/2 h-2.5 -translate-y-1/2 rounded-full bg-foreground/85"
          />
        ) : null}
        {points.map((point, index) => {
          const position = 4 + positions[index] * 92;
          const above = index % 2 === 1;
          const align = position < 14 ? "start" : position > 86 ? "end" : "center";
          return (
            <motion.div
              key={point.key}
              initial={false}
              animate={{ left: `${position}%` }}
              transition={springMove}
              className="absolute top-1/2 h-0 w-0"
            >
              <span
                className={cn(
                  "absolute top-0 left-0 block size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 ring-4 ring-surface",
                  point.problem
                    ? "border-destructive-text bg-destructive-text"
                    : point.key === "start" || point.key === "end"
                      ? "border-foreground bg-surface"
                      : "border-foreground bg-foreground",
                )}
              />
              <span
                className={cn(
                  "absolute flex w-28 flex-col text-[11px] leading-tight",
                  above ? "bottom-3" : "top-3",
                  align === "center" && "-translate-x-1/2 items-center text-center",
                  align === "start" && "-translate-x-2 items-start text-left",
                  align === "end" && "-translate-x-[calc(100%-0.5rem)] items-end text-right",
                )}
              >
                <span className={cn("font-medium", point.problem ? "text-destructive-text" : "text-foreground")}>{point.label}</span>
                <span className="text-muted-foreground tabular">
                  {inBrowser ? formatDateTime(new Date(point.at)) : `${formatDateTime(new Date(point.at), "UTC")} UTC`}
                </span>
              </span>
            </motion.div>
          );
        })}
      </div>
      <figcaption className="text-[13px] leading-relaxed text-muted-foreground">
        {problems.length ? (
          <span className="text-destructive-text">Some times are out of order. The fields above say what to change.</span>
        ) : sentences.length ? (
          <>Creators get {sentences.length > 1 ? `${sentences.slice(0, -1).join(", ")} and ${sentences[sentences.length - 1]}` : sentences[0]}.</>
        ) : (
          "Add the remaining times to see how long creators get for each part."
        )}
      </figcaption>
    </figure>
  );
}
