"use client";

import Link from "next/link";
import { ArrowUpRight, Send, Zap } from "lucide-react";
import { motion } from "motion/react";

import { XLogo } from "@/components/brand/social-icons";
import { BrandTile, brandWash } from "@/components/creator/brand-tile";
import { Money } from "@/components/creator/money";
import { pressed, springArrive, stagger } from "@/components/creator/motion";
import { SlotsMeter } from "@/components/creator/slots";
import { LocalWindow, TimeLeft, formatUtcWindow } from "@/components/creator/time";
import { Chip, NewBadge } from "@/components/creator/ui";
import { StatusBadge } from "@/components/status-badge";
import { platformLabel, type ClaimMode, type Platform } from "@/lib/campaigns/options";
import type { CampaignStatus, ClaimStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";

export type CampaignCardData = {
  href: string;
  brand: { name: string; initials: string; color?: string; handle?: string };
  title: string;
  summary: string;
  payout: { amount: string; currency: string };
  slots: { total: number; taken: number };
  platform: Platform;
  /** The deliverable's label, like "Quote post". */
  deliverable: string;
  postWindow: { start: string; end: string };
  status: CampaignStatus;
  isNew?: boolean;
  /** Counts down to the claim deadline when set (to the window otherwise). */
  claimDeadline?: string;
  claimMode?: ClaimMode;
  /** This creator's own claim, if they have one. */
  claimStatus?: ClaimStatus;
};

const NEUTRAL_BRAND = "#6b635f";

/**
 * A campaign as creators see it: the brand in its own color, the payout big,
 * how many slots are left, the window in local time plus UTC, and how long
 * claiming stays open. The whole card opens the campaign.
 *
 * Pass `index` to spring it in as part of a staggered list.
 */
function CampaignCard({
  campaign,
  className,
  index,
  layout = false,
}: {
  campaign: CampaignCardData;
  className?: string;
  index?: number;
  /** Glide to new positions when the list around it changes. */
  layout?: boolean;
}) {
  const color = campaign.brand.color ?? NEUTRAL_BRAND;
  const left = Math.max(0, campaign.slots.total - campaign.slots.taken);
  const full = campaign.status === "full" || left === 0;
  const closed = campaign.status === "closed" || campaign.status === "completed";
  const reveal = index !== undefined;

  return (
    <motion.article
      layout={layout ? "position" : false}
      initial={reveal ? { opacity: 0, y: 22, scale: 0.98 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.18 } }}
      transition={{ ...springArrive, delay: reveal ? stagger(index) : 0 }}
      whileHover={{ y: -5, transition: springArrive }}
      whileTap={pressed}
      className={cn(
        "group relative flex h-full flex-col overflow-hidden rounded-2xl border bg-surface shadow-soft",
        "transition-[border-color,box-shadow] duration-300 ease-snap hover:border-border-strong hover:shadow-float",
        "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background",
        className,
      )}
    >
      <div aria-hidden className="pointer-events-none absolute inset-0" style={brandWash(color, full ? 7 : 15)} />

      <div className="relative flex flex-1 flex-col gap-4 p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <BrandTile initials={campaign.brand.initials} color={color} size="md" className={cn(full && "saturate-50")} />
          <div className="min-w-0 flex-1 pt-0.5">
            <p className="truncate text-sm font-semibold tracking-[-0.01em]">{campaign.brand.name}</p>
            <p className="truncate text-xs text-muted-foreground">
              {campaign.brand.handle ?? `${platformLabel[campaign.platform]} campaign`}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {campaign.claimStatus ? (
              <span className="inline-flex h-6 items-center rounded-full bg-foreground px-2 text-[11px] font-semibold text-background">
                You&apos;re on it
              </span>
            ) : full || closed ? (
              <StatusBadge kind="campaign" status={closed ? campaign.status : "full"} />
            ) : campaign.isNew ? (
              <NewBadge />
            ) : null}
          </div>
        </div>

        <div className="min-w-0">
          <h3 className="flex items-start gap-1.5 text-[1.0625rem] leading-snug font-semibold tracking-[-0.022em] text-balance">
            <Link
              href={campaign.href}
              className="outline-none after:absolute after:inset-0 after:z-10 after:rounded-2xl focus-visible:outline-none"
            >
              {campaign.title}
            </Link>
            <ArrowUpRight
              aria-hidden
              className="mt-1 size-4 shrink-0 text-subtle-foreground opacity-0 transition-[opacity,transform] duration-300 ease-snap group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100"
            />
          </h3>
          <p className="mt-1 line-clamp-2 text-sm leading-relaxed text-pretty text-muted-foreground">{campaign.summary}</p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {campaign.claimStatus ? <StatusBadge kind="claim" status={campaign.claimStatus} className="h-7 px-2.5" /> : null}
          <Chip>
            {campaign.platform === "x" ? <XLogo className="size-3 text-foreground" /> : null}
            {campaign.platform === "x" ? campaign.deliverable : `${campaign.deliverable} on ${platformLabel[campaign.platform]}`}
          </Chip>
          {campaign.claimMode && !campaign.claimStatus ? (
            <Chip>
              {campaign.claimMode === "instant" ? <Zap /> : <Send />}
              {campaign.claimMode === "instant" ? "Instant claim" : "Apply to join"}
            </Chip>
          ) : null}
        </div>

        <div className="mt-auto flex items-end justify-between gap-4">
          <div className={cn("min-w-0", full && "opacity-60")}>
            <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="lg" />
            <p className="mt-1.5 text-xs text-muted-foreground">per post</p>
          </div>
          <div className="w-[7.75rem] shrink-0 text-right">
            <p className="text-sm leading-none whitespace-nowrap">
              {full ? (
                <span className="font-semibold">All {campaign.slots.total} taken</span>
              ) : (
                <>
                  <span className="font-semibold tabular">{left}</span>
                  <span className="text-muted-foreground"> of {campaign.slots.total} left</span>
                </>
              )}
            </p>
            <SlotsMeter total={campaign.slots.total} taken={campaign.slots.taken} className="mt-2.5" />
          </div>
        </div>
      </div>

      <div className="relative flex items-end justify-between gap-3 border-t bg-surface-2/45 px-4 py-3 sm:px-5">
        <div className="min-w-0 text-[13px] leading-snug">
          <LocalWindow start={campaign.postWindow.start} end={campaign.postWindow.end} className="block truncate font-medium" />
          <span className="block truncate text-xs text-muted-foreground">
            {formatUtcWindow(campaign.postWindow.start, campaign.postWindow.end)}
          </span>
        </div>
        <div className="shrink-0 text-right leading-snug">
          {full || closed ? (
            <>
              <span className="block text-[11px] text-muted-foreground">Claiming</span>
              <span className="text-[13px] font-semibold">{closed ? "Closed" : "Full"}</span>
            </>
          ) : campaign.claimDeadline ? (
            <>
              <span className="block text-[11px] text-muted-foreground">Claim closes in</span>
              <TimeLeft to={campaign.claimDeadline} endedLabel="Closed" className="font-mono text-[13px] font-semibold" />
            </>
          ) : (
            <>
              <span className="block text-[11px] text-muted-foreground">Opens in</span>
              <TimeLeft to={campaign.postWindow.start} endedLabel="Open now" className="font-mono text-[13px] font-semibold" />
            </>
          )}
        </div>
      </div>
    </motion.article>
  );
}

export { CampaignCard };
