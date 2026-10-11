"use client";

import { Check, CircleSlash, Clock } from "lucide-react";
import { motion } from "motion/react";

import { claimPath, pathPosition, type ClaimEvent, type CreatorClaim } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { claimStatusMeta, type ClaimStatus } from "@/lib/statuses";
import { formatUtcTime } from "@/lib/time";
import { cn } from "@/lib/utils";

import { springMove, springPop } from "../motion";
import { Ago, formatUtcWindow, LocalWhen, LocalWindow, TimeLeft } from "../time";
import { DetailSection } from "./brief";

type Moment = { key: string; label: string; start: string; end?: string };

/** Drop, claim deadline, post window and proof deadline on one rail, with where "now" is. */
export function TimingSection({ campaign, now }: { campaign: CreatorCampaign; now: number | null }) {
  const moments: Moment[] = [
    { key: "drop", label: "Dropped", start: campaign.droppedAt },
    { key: "claim", label: "Claiming closes", start: campaign.timing.claimDeadline },
    { key: "window", label: "Post window", start: campaign.timing.postWindowStart, end: campaign.timing.postWindowEnd },
    { key: "proof", label: "Proof due", start: campaign.timing.proofDeadline },
  ].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const doneAt = (moment: Moment) => new Date(moment.end ?? moment.start).getTime();
  const nextIndex = now === null ? -1 : moments.findIndex((moment) => doneAt(moment) > now);

  return (
    <DetailSection id="timing" kicker="Timing" title="When it happens">
      <ol className="relative flex flex-col">
        {moments.map((moment, index) => {
          const past = now !== null && doneAt(moment) <= now;
          const running = now !== null && moment.end !== undefined && new Date(moment.start).getTime() <= now && !past;
          const next = index === nextIndex;
          const last = index === moments.length - 1;
          return (
            <li key={moment.key} className="relative flex gap-4 pb-5 last:pb-0">
              {!last ? (
                <span aria-hidden className="absolute top-7 bottom-0 left-[13px] w-0.5 rounded-full bg-surface-3">
                  <motion.span
                    className="absolute inset-0 origin-top rounded-full bg-foreground/70"
                    initial={false}
                    animate={{ scaleY: past ? 1 : 0 }}
                    transition={springMove}
                  />
                </span>
              ) : null}
              <span
                className={cn(
                  "relative z-10 mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-300",
                  past
                    ? "border-foreground bg-foreground text-background"
                    : next || running
                      ? "border-foreground bg-surface text-foreground"
                      : "border-border-strong bg-surface text-subtle-foreground",
                )}
              >
                {past ? <Check className="size-3.5" strokeWidth={3} /> : <Clock className="size-3.5" />}
                {next || running ? (
                  <span aria-hidden className="absolute inset-0 animate-pulse-ring rounded-full border-2 border-foreground" />
                ) : null}
              </span>
              <div className={cn("min-w-0 flex-1", past && "opacity-60")}>
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <p className="text-sm font-semibold">{moment.label}</p>
                  {next && now !== null ? (
                    <TimeLeft
                      to={running && moment.end ? moment.end : moment.start}
                      prefix={running ? "Ends in" : "In"}
                      className="rounded-full bg-surface-2 px-2 py-0.5 font-mono text-xs font-medium"
                    />
                  ) : null}
                </div>
                {moment.end ? (
                  <>
                    <LocalWindow start={moment.start} end={moment.end} className="mt-0.5 block text-[15px]" />
                    <span className="block text-xs text-muted-foreground">{formatUtcWindow(moment.start, moment.end)}</span>
                  </>
                ) : (
                  <>
                    <LocalWhen value={moment.start} className="mt-0.5 block text-[15px]" />
                    <span className="block text-xs text-muted-foreground">{formatUtcTime(moment.start)}</span>
                  </>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-4 text-xs text-pretty text-muted-foreground">Times are in your time zone, with UTC underneath so everyone shares one clock.</p>
    </DetailSection>
  );
}

/** The step a loop-back event belongs under. */
function stepFor(status: ClaimStatus): ClaimStatus {
  if (status === "changes_requested") return "draft_submitted";
  if (status === "rejected") return "proof_submitted";
  return status;
}

function EventTime({ event }: { event?: ClaimEvent }) {
  if (!event?.at) return null;
  return <Ago value={event.at} className="shrink-0 text-xs text-muted-foreground tabular" />;
}

/**
 * Every step this claim goes through, from claim to paid. Changes asked for
 * and rejected proof show under the step they send you back to.
 */
export function StatusTimeline({ campaign, claim }: { campaign: CreatorCampaign; claim?: CreatorClaim }) {
  const path = claimPath(campaign);
  const events = claim?.events ?? [];
  const stopped = claim ? pathPosition(path, claim.status) < 0 : false;
  const reached = !claim
    ? -1
    : stopped
      ? Math.max(-1, ...events.map((event) => path.indexOf(stepFor(event.status))))
      : pathPosition(path, claim.status);
  const loopBack = claim?.status === "changes_requested" || claim?.status === "rejected";

  const steps: { status: ClaimStatus; state: "done" | "warn" | "next" | "todo" | "stopped" }[] = path.map((status, index) => ({
    status,
    state:
      index <= reached
        ? loopBack && index === reached
          ? "warn"
          : "done"
        : !stopped && index === reached + 1
          ? "next"
          : "todo",
  }));
  if (claim && stopped) {
    steps.splice(Math.max(0, reached + 1), steps.length, { status: claim.status, state: "stopped" });
  }

  return (
    <DetailSection
      id="status"
      kicker="Status"
      title={claim ? claimStatusMeta[claim.status].label : "How it goes"}
      action={
        claim ? null : <span className="mt-1 text-right text-xs text-muted-foreground">Your progress shows here once you claim</span>
      }
    >
      <ol className="flex flex-col">
        {steps.map((step, index) => {
          const meta = claimStatusMeta[step.status];
          const own = [...events].reverse().find((event) => event.status === step.status);
          const loops = events.filter(
            (event) => stepFor(event.status) === step.status && event.status !== step.status && event.note,
          );
          const notes: { text: string; label?: string; tone?: "amber" | "red" }[] = [
            ...(own?.note ? [{ text: own.note }] : []),
            ...loops.map((event) => ({
              text: event.note!,
              label: event.status === "rejected" ? "Sent back" : "Changes asked",
              tone: event.status === "rejected" ? ("red" as const) : ("amber" as const),
            })),
          ];
          const last = index === steps.length - 1;
          const filled = step.state === "done" || step.state === "warn";
          return (
            <li key={`${step.status}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
              {!last ? (
                <span aria-hidden className="absolute top-7 bottom-0 left-[13px] w-0.5 rounded-full bg-surface-3">
                  <motion.span
                    className="absolute inset-0 origin-top rounded-full bg-foreground/70"
                    initial={false}
                    animate={{ scaleY: filled && steps[index + 1]?.state !== "todo" ? 1 : 0 }}
                    transition={springMove}
                  />
                </span>
              ) : null}
              <motion.span
                key={step.state}
                initial={filled ? { scale: 0.6 } : false}
                animate={{ scale: 1 }}
                transition={springPop}
                data-tone={step.state === "warn" ? "amber" : step.state === "stopped" ? "gray" : undefined}
                className={cn(
                  "relative z-10 mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border-2",
                  step.state === "done" && "border-foreground bg-foreground text-background",
                  step.state === "warn" && "border-(--tone-fg) bg-(--tone-fg) text-background",
                  step.state === "next" && "border-foreground bg-surface",
                  step.state === "todo" && "border-border-strong bg-surface",
                  step.state === "stopped" && "border-(--tone-fg) bg-surface text-(--tone-fg)",
                )}
              >
                {step.state === "done" ? <Check className="size-3.5" strokeWidth={3} /> : null}
                {step.state === "warn" ? <span className="text-xs font-bold">!</span> : null}
                {step.state === "stopped" ? <CircleSlash className="size-3.5" /> : null}
                {step.state === "next" ? <span className="size-2 rounded-full bg-foreground" /> : null}
              </motion.span>
              <div className="min-w-0 flex-1 pt-0.5">
                <div className="flex items-baseline justify-between gap-3">
                  <p
                    className={cn(
                      "text-sm font-semibold",
                      step.state === "todo" && "font-medium text-muted-foreground",
                    )}
                  >
                    {step.state === "warn" ? claimStatusMeta[claim!.status].label : meta.label}
                    {step.state === "next" ? (
                      <span className="ml-2 rounded-full bg-surface-2 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        Up next
                      </span>
                    ) : null}
                  </p>
                  <EventTime event={step.state === "warn" ? [...events].reverse().find((event) => event.status === claim!.status) : own} />
                </div>
                {notes.length ? (
                  <ul className="mt-1.5 flex flex-col gap-1">
                    {notes.map((note, noteIndex) => (
                      <li
                        key={noteIndex}
                        data-tone={note.tone}
                        className="rounded-lg bg-surface-2/70 px-3 py-2 text-[13px] text-pretty text-muted-foreground"
                      >
                        {note.label ? <span className="mr-1.5 font-semibold text-(--tone-fg)">{note.label}:</span> : null}
                        {note.text}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </DetailSection>
  );
}
