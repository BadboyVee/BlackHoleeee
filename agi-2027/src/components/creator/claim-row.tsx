"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { motion } from "motion/react";

import { StatusBadge } from "@/components/status-badge";
import { claimClock, claimPath, nextStep, pathPosition, type CreatorClaim } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { claimStatusMeta } from "@/lib/statuses";
import { cn } from "@/lib/utils";

import { BrandTile } from "./brand-tile";
import { Money } from "./money";
import { pressed, springArrive, stagger } from "./motion";
import { LocalWhen, TimeLeft } from "./time";

/** "0x7c1e…a94f": long payment references, shortened for small screens. */
export function shortReference(reference: string) {
  return reference.length > 16 ? `${reference.slice(0, 6)}…${reference.slice(-4)}` : reference;
}

/** A thin row of segments: one per step on this claim's path, filled as it moves along. */
function ClaimProgress({
  campaign,
  status,
  className,
}: {
  campaign: Pick<CreatorCampaign, "claimMode" | "draftRequired">;
  status: CreatorClaim["status"];
  className?: string;
}) {
  const path = claimPath(campaign);
  const reached = pathPosition(path, status);
  const loopBack = status === "changes_requested" || status === "rejected";
  const label =
    reached < 0
      ? `Stopped: ${claimStatusMeta[status].label}`
      : `Step ${reached + 1} of ${path.length}: ${claimStatusMeta[status].label}`;

  return (
    <div role="img" aria-label={label} className={cn("flex h-1.5 gap-1", className)}>
      {path.map((step, index) => {
        const warn = loopBack && index === reached;
        const done = reached >= 0 && index <= reached;
        return (
          <span
            key={step}
            data-tone={warn ? "amber" : status === "paid" && done ? "brand" : undefined}
            className={cn(
              "h-full flex-1 rounded-full transition-colors duration-500 ease-snap",
              warn ? "bg-(--tone-fg)" : done ? (status === "paid" ? "bg-(--tone-fg)" : "bg-foreground/80") : "bg-surface-3",
              reached < 0 && "bg-surface-3",
            )}
          />
        );
      })}
    </div>
  );
}

/** The line under a claim: what's next and the clock that matters, or how it ended. */
function ClaimFooter({ campaign, claim, now }: { campaign: CreatorCampaign; claim: CreatorClaim; now: number | null }) {
  const step = nextStep(claim.status, campaign);
  if (claim.status === "paid") {
    return (
      <div className="flex items-center justify-between gap-3 text-[13px]">
        <span className="text-muted-foreground">
          Paid {claim.paidAt ? <LocalWhen value={claim.paidAt} className="text-foreground" /> : null}
        </span>
        {claim.paidReference ? (
          <span className="truncate font-mono text-xs text-muted-foreground">ref {shortReference(claim.paidReference)}</span>
        ) : null}
      </div>
    );
  }
  const clock = now === null ? null : claimClock(claim.status, campaign.timing, now);
  return (
    <div className="flex items-center justify-between gap-3 text-[13px]">
      <span className="min-w-0 truncate">
        <span className="font-medium">{step.title}</span>
        {step.actor === "agency" ? <span className="text-muted-foreground"> · with the agency</span> : null}
      </span>
      {clock ? (
        <TimeLeft to={clock.to} prefix={clock.label} className="shrink-0 font-mono text-xs font-medium" />
      ) : claim.status === "approved" ? (
        <StatusBadge kind="earning" status="unpaid" />
      ) : null}
    </div>
  );
}

/** One of your claims as a tappable card: brand, status, progress and what's next. */
function ClaimRow({
  campaign,
  claim,
  now,
  index = 0,
}: {
  campaign: CreatorCampaign;
  claim: CreatorClaim;
  now: number | null;
  index?: number;
}) {
  return (
    <motion.li
      layout="position"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.16 } }}
      transition={{ ...springArrive, delay: stagger(index) }}
      whileTap={pressed}
      className="list-none"
    >
      <Link
        href={`/dashboard/campaigns/${campaign.id}`}
        className="group flex flex-col gap-3.5 rounded-2xl border bg-surface p-4 shadow-soft transition-[border-color,box-shadow,transform] duration-300 ease-snap hover:-translate-y-0.5 hover:border-border-strong hover:shadow-float sm:p-5"
      >
        <div className="flex items-start gap-3">
          <BrandTile initials={campaign.brand.initials} color={campaign.brand.color} size="md" />
          <div className="min-w-0 flex-1">
            <p className="line-clamp-2 text-[15px] leading-snug font-semibold tracking-[-0.018em] text-pretty">{campaign.title}</p>
            <p className="mt-0.5 flex min-w-0 items-baseline gap-1.5 text-xs text-muted-foreground">
              <span className="truncate">{campaign.brand.name}</span>
              <span aria-hidden>·</span>
              <Money amount={claim.payout.amount} currency={claim.payout.currency} size="sm" className="text-foreground" />
            </p>
          </div>
          <ChevronRight className="mt-1 size-4 shrink-0 text-subtle-foreground transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge kind="claim" status={claim.status} />
          <ClaimProgress campaign={campaign} status={claim.status} className="flex-1" />
        </div>
        <ClaimFooter campaign={campaign} claim={claim} now={now} />
      </Link>
    </motion.li>
  );
}

export { ClaimProgress, ClaimRow };
