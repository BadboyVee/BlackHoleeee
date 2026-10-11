"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Tabs as TabsPrimitive } from "radix-ui";
import { BadgeCheck, History, Inbox, Megaphone, Wallet, type LucideIcon } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";

import { Skeleton } from "@/components/ui/skeleton";
import {
  claimClock,
  earningsFromClaims,
  earningsSummary,
  MY_CAMPAIGN_TABS,
  myCampaignTab,
  myCampaignTabMeta,
  type CreatorClaim,
  type MyCampaignTab,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { cn } from "@/lib/utils";

import { useClaims } from "./claim-store";
import { ClaimRow } from "./claim-row";
import { useCreatorDemo } from "./creator-data";
import { useHydrated, useNow } from "./hooks";
import { Money } from "./money";
import { pressed, springArrive, springMove } from "./motion";
import { displayType, panel } from "./ui";

const tabIcons: Record<MyCampaignTab, LucideIcon> = {
  active: Megaphone,
  submitted: Inbox,
  approved: BadgeCheck,
  paid: Wallet,
  past: History,
};

type Row = { campaign: CreatorCampaign; claim: CreatorClaim };

const lastEventAt = (claim: CreatorClaim) => {
  const stamped = [...claim.events].reverse().find((event) => event.at);
  return stamped?.at ? new Date(stamped.at).getTime() : 0;
};

function EmptyTab({ tab }: { tab: MyCampaignTab }) {
  const meta = myCampaignTabMeta[tab];
  const Icon = tabIcons[tab];
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springArrive}
      className={cn(panel, "flex flex-col items-center px-6 py-14 text-center shadow-none")}
    >
      <motion.span
        initial={{ scale: 0.7, rotate: -10 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={springArrive}
        className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground"
      >
        <Icon className="size-6" />
      </motion.span>
      <p className={cn(displayType, "text-2xl leading-none")}>{meta.empty}</p>
      <p className="mt-2 max-w-xs text-sm text-pretty text-muted-foreground">{meta.hint}</p>
      {tab === "active" || tab === "past" ? (
        <motion.div whileTap={pressed} className="mt-6">
          <Link
            href="/dashboard/campaigns"
            className="inline-flex h-11 items-center rounded-full bg-foreground px-5 text-sm font-semibold text-background"
          >
            Browse campaigns
          </Link>
        </motion.div>
      ) : null}
    </motion.div>
  );
}

function Totals({ rows, label }: { rows: Row[]; label: string }) {
  const summary = earningsSummary(earningsFromClaims(rows.map((row) => row.claim)));
  const totals = summary.total;
  if (totals.length === 0) return null;
  return (
    <div className="mb-3 flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-xl border bg-surface-2/50 px-4 py-3">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {totals.map((row) => (
        <Money key={row.currency} amount={row.amount} currency={row.currency} size="md" />
      ))}
      <span className="w-full text-xs text-subtle-foreground">Each currency on its own, never added together.</span>
    </div>
  );
}

/** Every claim you have, sorted into Active, Submitted, Approved, Paid and Past. */
function MyCampaigns() {
  const { campaigns } = useCreatorDemo();
  const claims = useClaims();
  const hydrated = useHydrated();
  const now = useNow(60_000);
  const [tab, setTab] = useState<MyCampaignTab>("active");

  const grouped = useMemo(() => {
    const byId = new Map(campaigns.map((campaign) => [campaign.id, campaign]));
    const groups = Object.fromEntries(MY_CAMPAIGN_TABS.map((key) => [key, [] as Row[]])) as Record<MyCampaignTab, Row[]>;
    for (const claim of claims) {
      const campaign = byId.get(claim.campaignId);
      if (campaign) groups[myCampaignTab(claim.status)].push({ campaign, claim });
    }
    const soonest = (row: Row) => {
      const clock = now === null ? null : claimClock(row.claim.status, row.campaign.timing, now);
      return clock ? new Date(clock.to).getTime() : new Date(row.campaign.timing.postWindowStart).getTime();
    };
    groups.active.sort((a, b) => soonest(a) - soonest(b));
    for (const key of ["submitted", "approved", "paid", "past"] as const) {
      groups[key].sort(
        (a, b) =>
          lastEventAt(b.claim) - lastEventAt(a.claim) ||
          new Date(b.campaign.timing.postWindowStart).getTime() - new Date(a.campaign.timing.postWindowStart).getTime(),
      );
    }
    return groups;
  }, [campaigns, claims, now]);

  return (
    <div className="flex flex-col gap-6">
      <header className="pt-2 sm:pt-4">
        <h1 className="text-h2">My campaigns</h1>
        <p className="mt-2 text-[15px] text-pretty text-muted-foreground sm:text-base">
          Everything you&apos;ve claimed, from first draft to paid.
        </p>
      </header>

      <TabsPrimitive.Root value={tab} onValueChange={(value) => setTab(value as MyCampaignTab)} className="flex flex-col gap-5">
        <TabsPrimitive.List
          aria-label="Claims by stage"
          className="grid grid-cols-5 gap-1 rounded-2xl border border-border-strong bg-surface p-1 shadow-soft sm:max-w-2xl"
        >
          {MY_CAMPAIGN_TABS.map((key) => {
            const on = key === tab;
            const count = grouped[key].length;
            return (
              <TabsPrimitive.Trigger
                key={key}
                value={key}
                className={cn(
                  "relative flex h-[4.25rem] min-w-0 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl px-1 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  on ? "text-background" : "text-muted-foreground hover:bg-surface-2/70 hover:text-foreground",
                )}
              >
                {on ? (
                  <motion.span
                    layoutId="my-campaigns-tab"
                    transition={springMove}
                    className="absolute inset-0 rounded-xl bg-foreground shadow-[0_8px_18px_-10px_rgb(var(--shadow-rgb)/0.6)]"
                  />
                ) : null}
                <span className={cn("relative text-figure text-[1.375rem] leading-none", !on && count === 0 && "text-subtle-foreground")}>
                  {hydrated ? count : "\u00a0"}
                </span>
                <span className="relative max-w-full truncate text-[11.5px] leading-none font-medium sm:text-xs">
                  {myCampaignTabMeta[key].label}
                </span>
              </TabsPrimitive.Trigger>
            );
          })}
        </TabsPrimitive.List>

        {MY_CAMPAIGN_TABS.map((key) => (
          <TabsPrimitive.Content key={key} value={key} className="outline-none">
            {!hydrated ? (
              <div className="flex flex-col gap-3">
                {[0, 1].map((row) => (
                  <Skeleton key={row} className="h-36 w-full rounded-2xl" />
                ))}
              </div>
            ) : grouped[key].length === 0 ? (
              <EmptyTab tab={key} />
            ) : (
              <>
                {key === "approved" ? <Totals rows={grouped[key]} label="Waiting to be paid" /> : null}
                {key === "paid" ? <Totals rows={grouped[key]} label="Paid to you" /> : null}
                <ul className="grid gap-3 lg:grid-cols-2">
                  <AnimatePresence initial={false}>
                    {grouped[key].map((row, index) => (
                      <ClaimRow key={row.campaign.id} campaign={row.campaign} claim={row.claim} now={now} index={index} />
                    ))}
                  </AnimatePresence>
                </ul>
              </>
            )}
          </TabsPrimitive.Content>
        ))}
      </TabsPrimitive.Root>
    </div>
  );
}

export { MyCampaigns };
