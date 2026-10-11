"use client";

import { useMemo, useSyncExternalStore } from "react";
import Link from "next/link";
import {
  BadgeCheck,
  Bell,
  CircleSlash,
  Coins,
  Link2,
  MessageSquareText,
  Sparkles,
  UserCheck,
  type LucideIcon,
} from "lucide-react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BOARD_STATUSES, isNewDrop } from "@/lib/campaigns/claims";
import { formatMoney } from "@/lib/money";
import type { ClaimStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";

import { BrandTile } from "./brand-tile";
import { useClaims } from "./claim-store";
import { useCreatorDemo } from "./creator-data";
import { useHydrated, useNow } from "./hooks";
import { pressed, springArrive, stagger } from "./motion";
import { Ago } from "./time";
import { displayType, panel } from "./ui";

/*
 * The demo's notifications, worked out from what already happened: every
 * agency move on your claims, plus fresh drops. "Mark all as read" is kept on
 * this device. Milestone 8 replaces this with real, live notifications.
 */

const READ_KEY = "agi-demo-notifications-read";
const READ_EVENT = "agi:demo-notifications-read";

function readMarker(): number {
  try {
    return Number(window.localStorage.getItem(READ_KEY) ?? 0) || 0;
  } catch {
    return 0;
  }
}

function subscribeMarker(onChange: () => void) {
  const onStorage = (event: StorageEvent) => {
    if (event.key === READ_KEY || event.key === null) onChange();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(READ_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(READ_EVENT, onChange);
  };
}

/** Marks everything up to the newest item as read (demo items can be dated ahead of today). */
function markAllRead(newest: number) {
  try {
    window.localStorage.setItem(READ_KEY, String(Math.max(Date.now(), newest)));
  } catch {
    // Storage blocked: nothing to remember.
  }
  window.dispatchEvent(new Event(READ_EVENT));
}

type Item = {
  id: string;
  at?: string;
  title: string;
  body: string;
  href: string;
  icon: LucideIcon;
  tone?: "amber" | "red" | "green" | "brand" | "blue";
  brand: { initials: string; color: string };
};

const agencyCopy: Partial<Record<ClaimStatus, { title: string; icon: LucideIcon; tone?: Item["tone"] }>> = {
  claimed: { title: "Request accepted", icon: UserCheck, tone: "green" },
  changes_requested: { title: "Changes requested", icon: MessageSquareText, tone: "amber" },
  draft_approved: { title: "Draft approved", icon: BadgeCheck, tone: "green" },
  rejected: { title: "Proof sent back", icon: Link2, tone: "red" },
  approved: { title: "Proof approved", icon: BadgeCheck, tone: "green" },
  paid: { title: "Payment sent", icon: Coins, tone: "brand" },
  expired: { title: "Claim expired", icon: CircleSlash },
  cancelled: { title: "Request declined", icon: CircleSlash },
};

/** Everything worth telling the creator, newest first, and how many are unread. */
export function useNotifications() {
  const { campaigns } = useCreatorDemo();
  const claims = useClaims();
  const now = useNow(60_000);
  const readAt = useSyncExternalStore(subscribeMarker, readMarker, () => 0);

  return useMemo(() => {
    const byId = new Map(campaigns.map((campaign) => [campaign.id, campaign]));
    const claimed = new Set(claims.map((claim) => claim.campaignId));
    const items: Item[] = [];

    for (const claim of claims) {
      const campaign = byId.get(claim.campaignId);
      if (!campaign) continue;
      claim.events.forEach((event, index) => {
        const copy = agencyCopy[event.status];
        if (event.by !== "agency" || !copy) return;
        const money = formatMoney(claim.payout.amount, claim.payout.currency);
        const body =
          event.status === "approved"
            ? `${money} for ${campaign.title} is on the way.`
            : event.status === "paid"
              ? `${money} for ${campaign.title}. ${event.note ?? ""}`.trim()
              : `${campaign.title}${event.note ? `: ${event.note}` : "."}`;
        items.push({
          id: `${claim.campaignId}-${index}`,
          at: event.at,
          title: copy.title,
          body,
          href: `/dashboard/campaigns/${campaign.id}`,
          icon: copy.icon,
          tone: copy.tone,
          brand: campaign.brand,
        });
      });
    }

    if (now !== null) {
      for (const campaign of campaigns) {
        if (!BOARD_STATUSES.includes(campaign.status) || campaign.status === "full" || claimed.has(campaign.id)) continue;
        if (campaign.slotsTaken >= campaign.slots) continue;
        if (!isNewDrop(campaign.droppedAt, now) || new Date(campaign.timing.claimDeadline).getTime() <= now) continue;
        items.push({
          id: `drop-${campaign.id}`,
          at: campaign.droppedAt,
          title: "New drop",
          body: `${campaign.brand.name}: ${campaign.title}. ${formatMoney(campaign.payout.amount, campaign.payout.currency)} per post.`,
          href: `/dashboard/campaigns/${campaign.id}`,
          icon: Sparkles,
          tone: "brand",
          brand: campaign.brand,
        });
      }
    }

    // Undated items are from before this preview started; they sort as the oldest.
    items.sort((a, b) => new Date(b.at ?? 0).getTime() - new Date(a.at ?? 0).getTime());
    const isUnread = (item: Item) => (item.at ? new Date(item.at).getTime() > readAt : readAt === 0);
    const newest = Math.max(0, ...items.map((item) => (item.at ? new Date(item.at).getTime() : 0)));
    return { items, unread: items.filter(isUnread).length, isUnread, newest };
  }, [campaigns, claims, now, readAt]);
}

/** The bell's dot: shown while anything is unread. */
export function NotificationDot({ className }: { className?: string }) {
  const hydrated = useHydrated();
  const { unread } = useNotifications();
  if (!hydrated || unread === 0) return null;
  return (
    <span aria-hidden className={cn("absolute flex size-2.5", className)}>
      <span className="absolute inset-0 animate-pulse-ring rounded-full bg-brand" />
      <span className="relative size-full rounded-full border-2 border-background bg-brand" />
    </span>
  );
}

export function CreatorNotifications() {
  const hydrated = useHydrated();
  const { items, unread, isUnread, newest } = useNotifications();

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4 pt-2 sm:pt-4">
        <div>
          <h1 className="text-h2">Notifications</h1>
          <p className="mt-2 text-[15px] text-pretty text-muted-foreground sm:text-base">
            Drops, approvals, change requests and payments, newest first.
          </p>
        </div>
        {hydrated && unread > 0 ? (
          <Button variant="secondary" size="lg" onClick={() => markAllRead(newest)}>
            Mark all as read
          </Button>
        ) : null}
      </header>

      {!hydrated ? (
        <Skeleton className="h-72 rounded-2xl" />
      ) : items.length === 0 ? (
        <div className={cn(panel, "flex flex-col items-center px-6 py-14 text-center shadow-none")}>
          <span className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground">
            <Bell className="size-6" />
          </span>
          <p className={cn(displayType, "text-2xl leading-none")}>All caught up</p>
          <p className="mt-2 max-w-xs text-sm text-pretty text-muted-foreground">
            New drops and every move on your claims show up here.
          </p>
        </div>
      ) : (
        <ul className={cn(panel, "divide-y overflow-hidden")}>
          {items.map((item, index) => {
            const Icon = item.icon;
            const fresh = isUnread(item);
            return (
              <motion.li
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springArrive, delay: stagger(index) }}
                whileTap={pressed}
              >
                <Link
                  href={item.href}
                  className={cn("flex items-start gap-3.5 p-4 transition-colors hover:bg-surface-2/60 sm:px-5", fresh && "bg-surface-2/40")}
                >
                  <span className="relative shrink-0">
                    <BrandTile initials={item.brand.initials} color={item.brand.color} size="md" />
                    <span
                      data-tone={item.tone}
                      className="absolute -right-1.5 -bottom-1.5 flex size-6 items-center justify-center rounded-full border-2 border-surface bg-surface text-(--tone-fg)"
                    >
                      <Icon className="size-3.5" />
                    </span>
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-3">
                      <span className="text-[15px] font-semibold tracking-[-0.015em]">{item.title}</span>
                      {item.at ? <Ago value={item.at} className="shrink-0 text-xs text-muted-foreground tabular" /> : null}
                    </span>
                    <span className="mt-0.5 line-clamp-2 block text-sm text-pretty text-muted-foreground">{item.body}</span>
                  </span>
                  {fresh ? <span aria-label="Unread" className="mt-2 size-2 shrink-0 rounded-full bg-brand" /> : null}
                </Link>
              </motion.li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
