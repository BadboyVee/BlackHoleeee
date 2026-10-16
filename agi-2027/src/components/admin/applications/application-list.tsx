"use client";

import { useCallback, useId, useMemo, useState } from "react";
import { motion } from "motion/react";
import { Inbox, UserCheck, Users, UserX } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ApplicationRow } from "@/lib/creators/queries";
import { cn } from "@/lib/utils";

import { springMove } from "../motion";
import { ApplicationCard } from "./application-card";
import {
  APPLICATION_TABS,
  applicationTabFrom,
  applicationTabHref,
  DEFAULT_TAB,
  rowsForTab,
  tabCounts,
  type ApplicationTab,
} from "./tabs";

const EMPTY: Record<ApplicationTab, { icon: React.ComponentType<{ className?: string }>; title: string; description: string }> = {
  waiting: {
    icon: Inbox,
    title: "Nothing waiting",
    description: "New applications land here and in your inbox.",
  },
  approved: {
    icon: UserCheck,
    title: "No one approved yet",
    description: "Creators you approve show up here, with who approved them and when.",
  },
  rejected: {
    icon: UserX,
    title: "No one rejected",
    description: "Applications you turn down show up here, with the team's notes.",
  },
  all: {
    icon: Users,
    title: "No applications yet",
    description: "When someone applies, their answers land here for you to approve or reject.",
  },
};

const ORDER_NOTE: Record<ApplicationTab, string> = {
  waiting: "Oldest first, so nobody waits too long.",
  approved: "Latest decisions first.",
  rejected: "Latest decisions first.",
  all: "Newest first.",
};

/**
 * Applications in four tabs: Waiting (the default), Approved, Rejected and
 * All. Arrow keys move between tabs. The tab sits in the address so a reload
 * opens the same view.
 */
export function ApplicationList({
  rows,
  initialTab = DEFAULT_TAB,
  preview = false,
}: {
  rows: ApplicationRow[];
  initialTab?: ApplicationTab;
  /** Sample data: nothing can be saved. */
  preview?: boolean;
}) {
  const [tab, setTab] = useState<ApplicationTab>(initialTab);
  // Decided from Waiting just now: kept in place to show the answer until the tab changes.
  const [kept, setKept] = useState<ReadonlySet<string>>(() => new Set());
  const indicatorId = useId();
  const counts = useMemo(() => tabCounts(rows), [rows]);
  const visible = useMemo(() => rowsForTab(rows, tab, kept), [rows, tab, kept]);

  const keep = useCallback((id: string) => {
    setKept((current) => (current.has(id) ? current : new Set(current).add(id)));
  }, []);

  function chooseTab(value: string) {
    const next = applicationTabFrom(value);
    setTab(next);
    setKept(new Set());
    window.history.replaceState(null, "", applicationTabHref(window.location.pathname, next));
  }

  return (
    <Tabs value={tab} onValueChange={chooseTab} className="max-w-5xl gap-4">
      <div className="-mx-4 overflow-x-auto px-4 [scrollbar-width:none] sm:mx-0 sm:px-0">
        <TabsList
          aria-label="Filter applications"
          className="flex h-auto w-max max-w-none min-w-full gap-0 overflow-visible rounded-none border-0 border-b bg-transparent p-0 sm:gap-1"
        >
          {APPLICATION_TABS.map((entry) => {
            const active = entry.id === tab;
            return (
              <TabsTrigger
                key={entry.id}
                value={entry.id}
                className={cn(
                  "relative h-11 gap-1 rounded-t-md rounded-b-none px-2 text-[13px] sm:gap-1.5 sm:px-3 sm:text-sm",
                  "outline-none focus-visible:bg-surface-2 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
                  "data-[state=active]:bg-transparent data-[state=active]:shadow-none",
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
                    layoutId={indicatorId}
                    transition={springMove}
                    aria-hidden
                    className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-foreground"
                  />
                ) : null}
              </TabsTrigger>
            );
          })}
        </TabsList>
      </div>

      {APPLICATION_TABS.map((entry) => (
        <TabsContent
          key={entry.id}
          value={entry.id}
          className="min-w-0 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
        >
          {entry.id === tab ? (
            <TabRows tab={tab} rows={visible} preview={preview} onReviewStart={keep} />
          ) : null}
        </TabsContent>
      ))}
    </Tabs>
  );
}

function TabRows({
  tab,
  rows,
  preview,
  onReviewStart,
}: {
  tab: ApplicationTab;
  rows: ApplicationRow[];
  preview: boolean;
  onReviewStart: (id: string) => void;
}) {
  if (rows.length === 0) {
    const empty = EMPTY[tab];
    return <EmptyState icon={empty.icon} title={empty.title} description={empty.description} />;
  }
  return (
    <>
      <p className="mb-3 text-[13px] text-muted-foreground">{ORDER_NOTE[tab]}</p>
      <ul className="grid grid-cols-1 gap-3">
        {rows.map((row) => (
          <li key={row.id} className="min-w-0">
            <ApplicationCard row={row} preview={preview} onReviewStart={onReviewStart} />
          </li>
        ))}
      </ul>
    </>
  );
}
