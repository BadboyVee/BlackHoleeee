"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { Megaphone, Plus, Search, X } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { deliverableMeta, platformLabel } from "@/lib/campaigns/options";
import { clientById, demoCampaigns, type DemoCampaign, type DemoClient } from "@/lib/campaigns/demo";
import { CAMPAIGN_STATUSES, campaignStatusMeta, type CampaignStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";
import { BrandTile } from "../brand-tile";
import { waitingCount } from "../demo-insights";
import { MoneyFigure } from "../money-figure";
import { springArrive, springMove } from "../motion";
import { LocalWindow, utcWindowText } from "../time-text";
import { CampaignRowActions } from "./campaign-actions";

type Tab = "all" | CampaignStatus;
type Sort = "status" | "window" | "newest" | "review";

const TABS: { id: Tab; label: string }[] = [
  { id: "all", label: "All" },
  { id: "live", label: "Live" },
  { id: "scheduled", label: "Scheduled" },
  { id: "draft", label: "Drafts" },
  { id: "full", label: "Full" },
  { id: "paused", label: "Paused" },
  { id: "closed", label: "Closed" },
  { id: "completed", label: "Completed" },
];

const SORTS: { id: Sort; label: string }[] = [
  { id: "status", label: "Status, then post window" },
  { id: "window", label: "Post window, soonest first" },
  { id: "newest", label: "Newest first" },
  { id: "review", label: "Most to review" },
];

/** Workflow order: what needs watching comes first. */
const statusOrder: Record<CampaignStatus, number> = {
  live: 0,
  full: 1,
  scheduled: 2,
  paused: 3,
  draft: 4,
  closed: 5,
  completed: 6,
};

type Row = { campaign: DemoCampaign; client: DemoClient | undefined; waiting: number };

const ROWS: Row[] = demoCampaigns.map((campaign) => ({
  campaign,
  client: clientById(campaign.clientId),
  waiting: waitingCount(campaign.id),
}));

function isTab(value: string | null): value is Tab {
  return value === "all" || (CAMPAIGN_STATUSES as readonly string[]).includes(value ?? "");
}

function sortRows(rows: Row[], sort: Sort) {
  const byWindow = (a: Row, b: Row) => a.campaign.timing.postWindowStart.localeCompare(b.campaign.timing.postWindowStart);
  return [...rows].sort((a, b) => {
    switch (sort) {
      case "status":
        return statusOrder[a.campaign.status] - statusOrder[b.campaign.status] || byWindow(a, b);
      case "window":
        return byWindow(a, b);
      case "newest":
        return b.campaign.createdAt.localeCompare(a.campaign.createdAt);
      case "review":
        return b.waiting - a.waiting || byWindow(a, b);
    }
  });
}

function matches(row: Row, query: string) {
  const haystack = [
    row.campaign.title,
    row.campaign.summary,
    row.client?.name,
    row.client?.xHandle,
    campaignStatusMeta[row.campaign.status].label,
    deliverableMeta[row.campaign.deliverable].label,
  ]
    .join(" ")
    .toLowerCase();
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => haystack.includes(word));
}

function SlotsCell({ campaign }: { campaign: DemoCampaign }) {
  const filled = campaign.slots ? campaign.slotsTaken / campaign.slots : 0;
  return (
    <div className="min-w-0">
      <p className="text-sm tabular">
        <span className="font-medium">{campaign.slotsTaken}</span>
        <span className="text-muted-foreground">/{campaign.slots}</span>
      </p>
      <div className="mt-1.5 h-1 w-16 overflow-hidden rounded-full bg-surface-3">
        <div
          className={cn("h-full rounded-full", filled >= 1 ? "bg-subtle-foreground" : "bg-foreground/70")}
          style={{ width: `${Math.round(filled * 100)}%` }}
        />
      </div>
    </div>
  );
}

function PayoutCell({ campaign }: { campaign: DemoCampaign }) {
  const custom = campaign.tierPayouts.length + campaign.creatorPayouts.length;
  return (
    <div>
      <MoneyFigure amount={campaign.payout.amount} currency={campaign.payout.currency} className="text-[15px]" />
      <p className="mt-0.5 text-xs text-subtle-foreground">{custom ? "Plus custom rates" : "Per post"}</p>
    </div>
  );
}

function ReviewCell({ waiting }: { waiting: number }) {
  if (!waiting) return <span className="text-sm text-subtle-foreground">None</span>;
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium tabular">
      <span aria-hidden className="size-1.5 rounded-full bg-(--tone-amber)" />
      {waiting}
      <span className="sr-only"> waiting for review</span>
    </span>
  );
}

function CampaignTitle({ row, stretch = true }: { row: Row; stretch?: boolean }) {
  const { campaign, client } = row;
  return (
    <div className="flex min-w-0 items-center gap-3">
      <BrandTile initials={client?.initials ?? "?"} color={client?.color} />
      <div className="min-w-0">
        <Link
          href={`/admin/campaigns/${campaign.id}`}
          className={cn(
            "block truncate text-sm font-medium text-foreground outline-none hover:underline hover:decoration-border-strong hover:underline-offset-4",
            stretch && "after:absolute after:inset-0 focus-visible:after:rounded-lg focus-visible:after:outline-2 focus-visible:after:outline-ring",
          )}
        >
          {campaign.title}
        </Link>
        <p className="truncate text-xs text-muted-foreground">
          {client?.name} · {deliverableMeta[campaign.deliverable].label} on {platformLabel[campaign.platform]}
        </p>
      </div>
    </div>
  );
}

export function CampaignList({ initialTab = "all" }: { initialTab?: Tab }) {
  const [tab, setTab] = useState<Tab>(initialTab);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<Sort>("status");

  const counts = useMemo(() => {
    const result: Record<Tab, number> = { all: ROWS.length } as Record<Tab, number>;
    for (const status of CAMPAIGN_STATUSES) result[status] = ROWS.filter((row) => row.campaign.status === status).length;
    return result;
  }, []);

  const rows = useMemo(() => {
    const inTab = tab === "all" ? ROWS : ROWS.filter((row) => row.campaign.status === tab);
    return sortRows(
      inTab.filter((row) => matches(row, query)),
      sort,
    );
  }, [tab, query, sort]);

  function chooseTab(next: Tab) {
    setTab(next);
    // Keep the tab in the address so a reload or a shared link opens the same view.
    const url = next === "all" ? window.location.pathname : `${window.location.pathname}?status=${next}`;
    window.history.replaceState(null, "", url);
  }

  const tabLabel = TABS.find((entry) => entry.id === tab)?.label ?? "All";

  return (
    <div className="flex flex-col gap-4">
      <div className="-mx-4 overflow-x-auto px-4 [scrollbar-width:none] sm:mx-0 sm:px-0">
        <div role="tablist" aria-label="Filter by status" className="flex w-max min-w-full items-center gap-1 border-b">
          {TABS.map((entry) => {
            const active = entry.id === tab;
            return (
              <button
                key={entry.id}
                type="button"
                role="tab"
                aria-selected={active}
                aria-controls="campaign-results"
                onClick={() => chooseTab(entry.id)}
                className={cn(
                  "relative flex h-11 shrink-0 cursor-pointer items-center gap-1.5 rounded-t-md px-3 text-sm font-medium transition-colors outline-none focus-visible:bg-surface-2",
                  active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {entry.label}
                <span
                  className={cn(
                    "min-w-5 rounded-full px-1.5 text-center font-mono text-[11px] leading-5 tabular",
                    active ? "bg-foreground text-background" : "bg-surface-2 text-muted-foreground",
                  )}
                >
                  {counts[entry.id]}
                </span>
                {active ? (
                  <motion.span
                    layoutId="campaign-tab"
                    transition={springMove}
                    aria-hidden
                    className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-foreground"
                  />
                ) : null}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <label className="relative flex-1 sm:max-w-sm">
          <span className="sr-only">Search campaigns</span>
          <Search aria-hidden className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-subtle-foreground" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by title or brand"
            className="h-11 w-full rounded-xl border border-input bg-surface pr-10 pl-10 text-base shadow-xs transition-[border-color,box-shadow] outline-none placeholder:text-subtle-foreground hover:border-border-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 sm:h-10 sm:text-sm [&::-webkit-search-cancel-button]:hidden"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="absolute top-1/2 right-1.5 flex size-8 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full text-muted-foreground hover:bg-surface-2 hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="size-4" />
            </button>
          ) : null}
        </label>
        <div className="flex items-center gap-2 sm:ml-auto">
          <span id="sort-label" className="text-[13px] whitespace-nowrap text-muted-foreground">
            Sort by
          </span>
          <Select value={sort} onValueChange={(value) => setSort(value as Sort)}>
            <SelectTrigger aria-labelledby="sort-label" className="h-11 w-full sm:h-10 sm:w-60">
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="end">
              {SORTS.map((option) => (
                <SelectItem key={option.id} value={option.id}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div id="campaign-results" role="tabpanel" aria-label={`${tabLabel} campaigns`} aria-live="polite">
        {rows.length === 0 ? (
          <EmptyState
            icon={Megaphone}
            title={query ? "No campaigns match" : `No ${tabLabel.toLowerCase()} campaigns`}
            description={
              query
                ? "Try a different word, or clear the search to see everything in this tab."
                : "Campaigns show up here when they reach this status."
            }
            action={
              query ? (
                <Button variant="secondary" onClick={() => setQuery("")}>
                  Clear search
                </Button>
              ) : (
                <Button asChild>
                  <Link href="/admin/campaigns/new">
                    <Plus aria-hidden />
                    New campaign
                  </Link>
                </Button>
              )
            }
          />
        ) : (
          <>
            {/* Desktop and tablet: a dense table. */}
            <div className="hidden overflow-hidden rounded-lg border bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)] md:block">
              <table className="w-full table-fixed text-left">
                <caption className="sr-only">
                  {tabLabel} campaigns, {rows.length} shown
                </caption>
                <colgroup>
                  <col />
                  <col className="w-[7.5rem]" />
                  <col className="w-[5.5rem]" />
                  <col className="w-[8.5rem]" />
                  <col className="hidden w-[16rem] lg:table-column" />
                  <col className="w-[5.5rem]" />
                  <col className="w-14" />
                </colgroup>
                <thead>
                  <tr className="border-b bg-surface-2/40 text-label text-subtle-foreground">
                    <th scope="col" className="py-2.5 pr-3 pl-5 font-medium">Campaign</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Status</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Slots</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Payout</th>
                    <th scope="col" className="hidden px-3 py-2.5 font-medium lg:table-cell">Post window</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Review</th>
                    <th scope="col" className="py-2.5 pr-3 pl-1 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence initial={false}>
                    {rows.map((row) => (
                      <motion.tr
                        key={row.campaign.id}
                        layout="position"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ opacity: { duration: 0.12 }, layout: springMove }}
                        className="group relative border-b transition-colors last:border-b-0 hover:bg-surface-2/50"
                      >
                        <td className="py-3 pr-3 pl-5">
                          <CampaignTitle row={row} />
                        </td>
                        <td className="px-3 py-3">
                          <StatusBadge kind="campaign" status={row.campaign.status} />
                        </td>
                        <td className="px-3 py-3">
                          <SlotsCell campaign={row.campaign} />
                        </td>
                        <td className="px-3 py-3">
                          <PayoutCell campaign={row.campaign} />
                        </td>
                        <td className="hidden px-3 py-3 lg:table-cell">
                          <LocalWindow
                            start={row.campaign.timing.postWindowStart}
                            end={row.campaign.timing.postWindowEnd}
                            className="block truncate text-[13px]"
                          />
                          <span className="mt-0.5 block truncate text-xs text-subtle-foreground">
                            {utcWindowText(row.campaign.timing.postWindowStart, row.campaign.timing.postWindowEnd)}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <ReviewCell waiting={row.waiting} />
                        </td>
                        <td className="py-3 pr-3 pl-1 text-right">
                          <CampaignRowActions id={row.campaign.id} title={row.campaign.title} status={row.campaign.status} />
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            {/* Phones: cards. */}
            <ul className="flex flex-col gap-2.5 md:hidden">
              <AnimatePresence initial={false}>
                {rows.map((row) => (
                  <motion.li
                    key={row.campaign.id}
                    layout="position"
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={springArrive}
                    className="relative rounded-lg border bg-surface p-4 shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)]"
                  >
                    <div className="flex items-start gap-3">
                      <div className="min-w-0 flex-1">
                        <CampaignTitle row={row} />
                      </div>
                      <CampaignRowActions
                        id={row.campaign.id}
                        title={row.campaign.title}
                        status={row.campaign.status}
                        className="-mt-1 -mr-2"
                      />
                    </div>
                    <div className="mt-3.5 flex flex-wrap items-center gap-x-4 gap-y-2">
                      <StatusBadge kind="campaign" status={row.campaign.status} />
                      <MoneyFigure amount={row.campaign.payout.amount} currency={row.campaign.payout.currency} className="text-sm" />
                      <span className="text-[13px] text-muted-foreground tabular">
                        {row.campaign.slotsTaken}/{row.campaign.slots} slots
                      </span>
                      {row.waiting ? (
                        <span className="inline-flex items-center gap-1.5 text-[13px] font-medium">
                          <span aria-hidden className="size-1.5 rounded-full bg-(--tone-amber)" />
                          {row.waiting} to review
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-3 border-t pt-3 text-[13px]">
                      <LocalWindow
                        start={row.campaign.timing.postWindowStart}
                        end={row.campaign.timing.postWindowEnd}
                        className="block"
                      />
                      <span className="block text-xs text-subtle-foreground">
                        {utcWindowText(row.campaign.timing.postWindowStart, row.campaign.timing.postWindowEnd)}
                      </span>
                    </div>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

/** Reads ?status= so links like the overview's "Live campaigns" open the right tab. */
export function CampaignListFromUrl() {
  const params = useSearchParams();
  const status = params.get("status");
  return <CampaignList initialTab={isTab(status) ? status : "all"} />;
}
