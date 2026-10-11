"use client";

import { useMemo, useState } from "react";
import { ArrowDownUp, Calendar, Check, ChevronDown, Coins, Search, SearchX, X } from "lucide-react";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";

import { XLogo } from "@/components/brand/social-icons";
import { CampaignCard } from "@/components/campaign/campaign-card";
import { toCardData } from "@/components/campaign/card-data";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BOARD_STATUSES,
  dateBucket,
  sortCampaigns,
  type BoardSort,
  type DateBucket,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { deliverableMeta, platformLabel, type Platform } from "@/lib/campaigns/options";
import { cn } from "@/lib/utils";

import { useClaims } from "./claim-store";
import { useCreatorDemo } from "./creator-data";
import { useHydrated, useNow } from "./hooks";
import { pressed, springArrive, springMove } from "./motion";
import { displayType, panel } from "./ui";

type StatusFilter = "all" | "open" | "full";
type Filters = {
  platform: Platform | "all";
  currency: string;
  date: DateBucket | "any";
  status: StatusFilter;
  sort: BoardSort;
  query: string;
};

const DEFAULTS: Filters = { platform: "all", currency: "all", date: "any", status: "all", sort: "newest", query: "" };

const dateLabels: Record<DateBucket | "any", string> = {
  any: "Any time",
  today: "Today",
  week: "This week",
  later: "Later",
};
const sortLabels: Record<BoardSort, { label: string; hint: string }> = {
  newest: { label: "Newest", hint: "Latest drops first" },
  payout: { label: "Highest payout", hint: "Within each currency, never converted" },
  ending: { label: "Ending soon", hint: "Claim deadline closest first" },
};

function matches(campaign: CreatorCampaign, query: string) {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;
  const haystack = [
    campaign.title,
    campaign.summary,
    campaign.brand.name,
    campaign.brand.xHandle,
    platformLabel[campaign.platform],
    deliverableMeta[campaign.deliverable].label,
    ...campaign.requiredTags.mentions,
    ...campaign.requiredTags.hashtags,
    ...campaign.requiredTags.keywords,
  ]
    .join(" ")
    .toLowerCase();
  return needle.split(/\s+/).every((word) => haystack.includes(word));
}

function PlatformGlyph({ className }: { className?: string }) {
  return <XLogo className={cn("size-3.5", className)} />;
}

/** A chip that opens a small menu of choices. Filled when it's narrowing the list. */
function FilterMenu<T extends string>({
  icon: Icon,
  label,
  value,
  options,
  active,
  onChange,
  heading,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: T;
  options: { value: T; label: string; hint?: string; count?: number }[];
  active: boolean;
  onChange: (value: T) => void;
  heading: string;
}) {
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <motion.button
          type="button"
          whileTap={pressed}
          className={cn(
            "inline-flex h-11 shrink-0 cursor-pointer items-center gap-2 rounded-full border pr-3 pl-3.5 text-sm font-medium whitespace-nowrap transition-colors outline-none",
            active
              ? "border-foreground bg-foreground text-background"
              : "border-border-strong bg-surface text-foreground hover:bg-surface-2",
          )}
        >
          <Icon className="size-4 opacity-80" />
          {label}
          <ChevronDown className="size-3.5 opacity-70" />
        </motion.button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">{heading}</DropdownMenuLabel>
        {options.map((option) => (
          <DropdownMenuItem key={option.value} onSelect={() => onChange(option.value)} className="justify-between gap-3">
            <span className="flex min-w-0 flex-col">
              <span className={cn("truncate", option.value === value && "font-semibold")}>{option.label}</span>
              {option.hint ? <span className="truncate text-xs text-muted-foreground">{option.hint}</span> : null}
            </span>
            <span className="flex shrink-0 items-center gap-2">
              {option.count !== undefined ? (
                <span className="text-xs text-muted-foreground tabular">{option.count}</span>
              ) : null}
              {option.value === value ? <Check className="size-4 text-brand-text" /> : <span className="size-4" />}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** All, Open, Full: a segmented control with a sliding pill. */
function StatusSwitch({
  value,
  counts,
  onChange,
}: {
  value: StatusFilter;
  counts: Record<StatusFilter, number>;
  onChange: (value: StatusFilter) => void;
}) {
  const items: { value: StatusFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "open", label: "Open" },
    { value: "full", label: "Full" },
  ];
  return (
    <div role="radiogroup" aria-label="Status" className="inline-flex h-11 shrink-0 items-center gap-0.5 rounded-full border border-border-strong bg-surface p-1">
      {items.map((item) => {
        const on = item.value === value;
        return (
          <motion.button
            key={item.value}
            type="button"
            role="radio"
            aria-checked={on}
            whileTap={pressed}
            onClick={() => onChange(item.value)}
            className={cn(
              "relative inline-flex h-full cursor-pointer items-center gap-1.5 rounded-full px-3.5 text-sm font-medium transition-colors",
              on ? "text-background" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {on ? (
              <motion.span layoutId="board-status-pill" transition={springMove} className="absolute inset-0 rounded-full bg-foreground" />
            ) : null}
            <span className="relative">{item.label}</span>
            <span className={cn("relative text-xs tabular", on ? "text-background/70" : "text-subtle-foreground")}>
              {counts[item.value]}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}

function BoardSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {[0, 1, 2, 3].map((key) => (
        <div key={key} className={cn(panel, "flex h-[23rem] flex-col gap-4 p-5")}>
          <div className="flex items-center gap-3">
            <Skeleton className="size-11 rounded-xl" />
            <div className="flex flex-1 flex-col gap-2">
              <Skeleton className="h-3.5 w-28" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-5 w-4/5" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="mt-auto h-9 w-36" />
        </div>
      ))}
    </div>
  );
}

/** Every campaign open to this creator, with search, filters and sorting. */
function CampaignBoard() {
  const { campaigns, claims: seed } = useCreatorDemo();
  const claims = useClaims();
  const now = useNow(60_000);
  const hydrated = useHydrated();
  const [filters, setFilters] = useState<Filters>(DEFAULTS);
  const set = <K extends keyof Filters>(key: K, value: Filters[K]) => setFilters((current) => ({ ...current, [key]: value }));

  const board = useMemo(() => {
    const claimFor = new Map(claims.map((claim) => [claim.campaignId, claim]));
    const seedFor = new Map(seed.map((claim) => [claim.campaignId, claim.status]));
    return campaigns
      .filter((campaign) => BOARD_STATUSES.includes(campaign.status))
      .map((campaign) => {
        const card = toCardData(campaign, { claim: claimFor.get(campaign.id), seedStatus: seedFor.get(campaign.id), now });
        const deadlinePassed = now !== null && new Date(campaign.timing.claimDeadline).getTime() <= now;
        return { campaign, card, open: card.status === "live" && !deadlinePassed, full: card.status === "full" };
      });
  }, [campaigns, claims, seed, now]);

  const options = useMemo(() => {
    const count = <T,>(pick: (row: (typeof board)[number]) => T) => {
      const map = new Map<T, number>();
      for (const row of board) map.set(pick(row), (map.get(pick(row)) ?? 0) + 1);
      return map;
    };
    return {
      platforms: count((row) => row.campaign.platform),
      currencies: count((row) => row.campaign.payout.currency),
      dates: now === null ? new Map<DateBucket, number>() : count((row) => dateBucket(row.campaign.timing.postWindowStart, now)),
    };
  }, [board, now]);

  const visible = useMemo(() => {
    const rows = board.filter(({ campaign, open, full }) => {
      if (filters.platform !== "all" && campaign.platform !== filters.platform) return false;
      if (filters.currency !== "all" && campaign.payout.currency !== filters.currency) return false;
      if (filters.date !== "any" && (now === null || dateBucket(campaign.timing.postWindowStart, now) !== filters.date)) return false;
      if (filters.status === "open" && !open) return false;
      if (filters.status === "full" && !full) return false;
      return matches(campaign, filters.query);
    });
    const sorted = sortCampaigns(
      rows.map((row) => ({ ...row, droppedAt: row.campaign.droppedAt, payout: row.campaign.payout, timing: row.campaign.timing })),
      filters.sort,
      now ?? 0,
    );
    return sorted;
  }, [board, filters, now]);

  const statusCounts: Record<StatusFilter, number> = {
    all: board.length,
    open: board.filter((row) => row.open).length,
    full: board.filter((row) => row.full).length,
  };
  const narrowed =
    filters.platform !== DEFAULTS.platform ||
    filters.currency !== DEFAULTS.currency ||
    filters.date !== DEFAULTS.date ||
    filters.status !== DEFAULTS.status ||
    filters.query.trim() !== "";
  const claimable = board.filter((row) => row.open && !row.card.claimStatus).length;
  const newCount = board.filter((row) => row.open && row.card.isNew).length;

  return (
    <div className="flex flex-col gap-6">
      <header className="pt-2 sm:pt-4">
        <h1 className="text-h2">Campaigns</h1>
        <p className="mt-2 min-h-[1.5em] text-[15px] text-pretty text-muted-foreground sm:text-base">
          {hydrated ? (
            <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              {claimable === 0
                ? "Nothing new to claim right now. New drops land here first."
                : `${claimable} you can claim${newCount ? `, ${newCount} new` : ""}. Instant slots go first come, first served.`}
            </motion.span>
          ) : (
            "Every campaign open to you, with payout, slots and timing."
          )}
        </p>
      </header>

      <div className="flex flex-col gap-3">
        <label className="relative block">
          <span className="sr-only">Search campaigns</span>
          <Search aria-hidden className="pointer-events-none absolute top-1/2 left-4 size-[18px] -translate-y-1/2 text-subtle-foreground" />
          <input
            type="search"
            value={filters.query}
            onChange={(event) => set("query", event.target.value)}
            placeholder="Search brands, titles or tags"
            className="h-12 w-full rounded-full border border-input bg-surface pr-12 pl-11 text-base shadow-xs transition-[border-color,box-shadow] outline-none placeholder:text-subtle-foreground hover:border-border-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15 sm:text-[15px] [&::-webkit-search-cancel-button]:hidden"
          />
          <AnimatePresence>
            {filters.query ? (
              <motion.button
                type="button"
                aria-label="Clear search"
                onClick={() => set("query", "")}
                initial={{ opacity: 0, scale: 0.6 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.6 }}
                transition={springArrive}
                className="absolute top-1/2 right-1 flex size-10 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full text-muted-foreground hover:bg-surface-2 hover:text-foreground"
              >
                <X className="size-4" />
              </motion.button>
            ) : null}
          </AnimatePresence>
        </label>

        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [mask-image:linear-gradient(to_right,#000_85%,transparent)] [scrollbar-width:none] sm:-mx-6 sm:px-6 lg:mx-0 lg:flex-wrap lg:px-0 lg:[mask-image:none] [&::-webkit-scrollbar]:hidden">
          <LayoutGroup id="board-status">
            <StatusSwitch value={filters.status} counts={statusCounts} onChange={(value) => set("status", value)} />
          </LayoutGroup>
          <FilterMenu
            icon={Calendar}
            heading="When the post window starts"
            label={filters.date === "any" ? "Date" : dateLabels[filters.date]}
            value={filters.date}
            active={filters.date !== "any"}
            onChange={(value) => set("date", value)}
            options={(["any", "today", "week", "later"] as const).map((value) => ({
              value,
              label: dateLabels[value],
              count: value === "any" ? board.length : (options.dates.get(value) ?? 0),
            }))}
          />
          <FilterMenu
            icon={Coins}
            heading="Payout currency"
            label={filters.currency === "all" ? "Payout" : filters.currency}
            value={filters.currency}
            active={filters.currency !== "all"}
            onChange={(value) => set("currency", value)}
            options={[
              { value: "all", label: "Any currency", count: board.length },
              ...[...options.currencies].map(([currency, count]) => ({ value: currency, label: currency, count })),
            ]}
          />
          <FilterMenu
            icon={PlatformGlyph}
            heading="Platform"
            label={filters.platform === "all" ? "Platform" : platformLabel[filters.platform]}
            value={filters.platform}
            active={filters.platform !== "all"}
            onChange={(value) => set("platform", value)}
            options={[
              { value: "all" as const, label: "Any platform", count: board.length },
              ...[...options.platforms].map(([platform, count]) => ({ value: platform, label: platformLabel[platform], count })),
            ]}
          />
          <FilterMenu
            icon={ArrowDownUp}
            heading="Sort by"
            label={sortLabels[filters.sort].label}
            value={filters.sort}
            active={false}
            onChange={(value) => set("sort", value)}
            options={(["newest", "payout", "ending"] as const).map((value) => ({
              value,
              label: sortLabels[value].label,
              hint: sortLabels[value].hint,
            }))}
          />
        </div>

        <div className="flex h-6 items-center justify-between gap-3 text-[13px] text-muted-foreground">
          <span aria-live="polite">
            {hydrated ? `Showing ${visible.length} of ${board.length}` : " "}
          </span>
          <AnimatePresence>
            {narrowed ? (
              <motion.button
                type="button"
                onClick={() => setFilters((current) => ({ ...DEFAULTS, sort: current.sort }))}
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={springArrive}
                className="-mr-2 inline-flex h-11 cursor-pointer items-center gap-1 rounded-full px-2 font-medium text-foreground hover:bg-surface-2"
              >
                <X className="size-3.5" />
                Clear filters
              </motion.button>
            ) : null}
          </AnimatePresence>
        </div>
      </div>

      {!hydrated ? (
        <BoardSkeleton />
      ) : visible.length ? (
        <motion.div layout className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <AnimatePresence mode="popLayout" initial={false}>
            {visible.map((row, index) => (
              <motion.div
                key={row.campaign.id}
                layout="position"
                exit={{ opacity: 0, scale: 0.94, transition: { duration: 0.16 } }}
                transition={springMove}
                className="min-w-0"
              >
                <CampaignCard campaign={row.card} index={index} />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={springArrive}
          className={cn(panel, "flex flex-col items-center px-6 py-14 text-center shadow-none")}
        >
          <motion.span
            initial={{ rotate: -12, scale: 0.8 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={springArrive}
            className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground"
          >
            <SearchX className="size-6" />
          </motion.span>
          <p className={cn(displayType, "text-2xl leading-none")}>Nothing matches</p>
          <p className="mt-2 max-w-xs text-sm text-pretty text-muted-foreground">
            {filters.date === "today"
              ? "No windows open today. Try this week or later."
              : "Try another date or currency, or clear the filters to see everything open to you."}
          </p>
          <motion.button
            type="button"
            whileTap={pressed}
            onClick={() => setFilters((current) => ({ ...DEFAULTS, sort: current.sort }))}
            className="mt-6 inline-flex h-11 cursor-pointer items-center gap-2 rounded-full bg-foreground px-5 text-sm font-semibold text-background"
          >
            Clear filters
          </motion.button>
        </motion.div>
      )}
    </div>
  );
}

export { CampaignBoard };
