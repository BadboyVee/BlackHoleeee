import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { BrandTile, brandInitials } from "@/components/admin/brand-tile";
import {
  campaignStats,
  campaignsByStatus,
  DEMO_NOW,
  demoApplications,
  demoLeads,
  paidThisMonth,
  postsDueToday,
  reviewQueue,
  unpaidTotals,
  type ReviewItem,
} from "@/components/admin/demo-insights";
import { MoneyList } from "@/components/admin/money-figure";
import { ActivityChart } from "@/components/admin/overview/activity-chart";
import { Panel } from "@/components/admin/panel";
import { LocalWhen } from "@/components/admin/time-text";
import { StatusBadge } from "@/components/status-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { clientById, demoCampaigns, type DemoCampaign } from "@/lib/campaigns/demo";
import type { ClaimStatus } from "@/lib/statuses";
import { formatCountdown } from "@/lib/time";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: "Overview" };

const nowMs = new Date(DEMO_NOW).getTime();
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

const reviewStatus: Record<ReviewItem["kind"], ClaimStatus> = {
  Request: "requested",
  Draft: "draft_submitted",
  Proof: "proof_submitted",
};

function plural(count: number, one: string, many = `${one}s`) {
  return `${count} ${count === 1 ? one : many}`;
}

type Kpi = { label: string; value: number; detail: React.ReactNode; href: string; attention?: boolean };

function KpiStrip({ items }: { items: Kpi[] }) {
  return (
    <div className="grid grid-cols-2 overflow-hidden rounded-lg border bg-border shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)] [gap:1px] sm:grid-cols-3 xl:grid-cols-6">
      {items.map((item) => (
        <Link
          key={item.label}
          href={item.href}
          className="group relative flex min-h-[7.25rem] flex-col justify-between bg-surface p-4 transition-colors hover:bg-surface-2/50 sm:p-5"
        >
          <span className="flex items-start justify-between gap-2 text-[13px] text-muted-foreground">
            {item.label}
            <ArrowUpRight
              aria-hidden
              className="size-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
            />
          </span>
          <span className="mt-3 flex items-center gap-2">
            <span className="text-figure text-[1.875rem] leading-none">{item.value}</span>
            {item.attention && item.value > 0 ? (
              <span aria-hidden className="relative flex size-2 text-(--tone-amber)" data-tone="amber">
                <span className="absolute inset-0 animate-pulse-ring rounded-full bg-current" />
                <span className="relative size-full rounded-full bg-current" />
              </span>
            ) : null}
          </span>
          <span className="mt-2 line-clamp-2 text-xs leading-snug text-muted-foreground">{item.detail}</span>
        </Link>
      ))}
    </div>
  );
}

type UpcomingEvent = { at: string; label: string; campaign: DemoCampaign };

function upcomingEvents(): UpcomingEvent[] {
  const events: UpcomingEvent[] = [];
  for (const campaign of demoCampaigns) {
    if (campaign.status === "draft" || campaign.status === "completed" || campaign.status === "closed") continue;
    const t = campaign.timing;
    if (campaign.status === "scheduled" && t.dropAt) events.push({ at: t.dropAt, label: "Drops to creators", campaign });
    if (campaign.status !== "full") events.push({ at: t.claimDeadline, label: "Claiming closes", campaign });
    events.push({ at: t.postWindowStart, label: "Post window opens", campaign });
    events.push({ at: t.postWindowEnd, label: "Post window closes", campaign });
    events.push({ at: t.proofDeadline, label: "Proof is due", campaign });
  }
  return events
    .filter((event) => new Date(event.at).getTime() > nowMs)
    .sort((a, b) => a.at.localeCompare(b.at))
    .slice(0, 7);
}

function ReviewRow({ item }: { item: ReviewItem }) {
  return (
    <li className="flex items-center gap-3 px-4 py-3 sm:px-5">
      <Avatar className="size-9">
        <AvatarFallback>{brandInitials(item.creator.name)}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
          <p className="truncate text-sm font-medium">{item.creator.name}</p>
          <StatusBadge kind="claim" status={reviewStatus[item.kind]} />
        </div>
        <p className="mt-0.5 truncate text-[13px] text-muted-foreground">
          {item.campaign.title}
          <span className="text-subtle-foreground"> · {item.client?.name}</span>
        </p>
      </div>
      <div className="hidden shrink-0 text-right sm:block">
        <p className="text-[11px] text-subtle-foreground">Waiting</p>
        <p className="font-mono text-[13px] font-medium tabular">{formatCountdown(item.waitingMs)}</p>
      </div>
      <Button asChild variant="secondary" size="sm" className="shrink-0">
        <Link href="/admin/review" aria-label={`Review ${item.kind.toLowerCase()} from ${item.creator.name}`}>
          Review
        </Link>
      </Button>
    </li>
  );
}

export default function AdminOverviewPage() {
  const queue = reviewQueue();
  const live = campaignsByStatus("live");
  const full = campaignsByStatus("full");
  const paused = campaignsByStatus("paused");
  const scheduled = campaignsByStatus("scheduled");
  const due = postsDueToday();
  const dueCampaigns = [...new Set(due.map((entry) => entry.campaign.title))];
  const counts = {
    proofs: queue.filter((item) => item.kind === "Proof").length,
    drafts: queue.filter((item) => item.kind === "Draft").length,
    requests: queue.filter((item) => item.kind === "Request").length,
  };
  const today = DEMO_NOW.slice(0, 10);
  const inFlight = [...live, ...full, ...paused];
  const events = upcomingEvents();
  const nextDrop = scheduled[0]?.timing.dropAt;

  const kpis: Kpi[] = [
    {
      label: "Live campaigns",
      value: live.length,
      detail: `${plural(full.length, "full")}, ${plural(paused.length, "paused", "paused")}`,
      href: "/admin/campaigns?status=live",
    },
    {
      label: "Posts due today",
      value: due.length,
      detail: dueCampaigns.length ? `On ${dueCampaigns.join(", ")}` : "Nothing due",
      href: due[0] ? `/admin/campaigns/${due[0].campaign.id}` : "/admin/campaigns",
    },
    {
      label: "Waiting for review",
      value: queue.length,
      detail: `${plural(counts.proofs, "proof")}, ${plural(counts.drafts, "draft")}, ${plural(counts.requests, "request")}`,
      href: "/admin/review",
      attention: true,
    },
    {
      label: "Scheduled drops",
      value: scheduled.length,
      detail: nextDrop ? (
        <>
          Next <LocalWhen value={nextDrop} />
        </>
      ) : (
        "None scheduled"
      ),
      href: "/admin/campaigns?status=scheduled",
    },
    {
      label: "New applications",
      value: demoApplications.length,
      detail: `${demoApplications.filter((entry) => entry.at.startsWith(today)).length} today`,
      href: "/admin/applications",
    },
    {
      label: "New leads",
      value: demoLeads.length,
      detail: `${demoLeads.filter((entry) => entry.at.startsWith(today)).length} today`,
      href: "/admin/leads",
    },
  ];

  return (
    <>
      <AdminPageHeader
        title="Overview"
        description={
          <>
            {plural(queue.length, "item")} waiting for review and {plural(due.length, "post")} due today.
          </>
        }
        actions={
          <Button asChild variant="secondary">
            <Link href="/admin/review">
              Open review queue
              <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          </Button>
        }
      />

      <KpiStrip items={kpis} />

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <Panel
          id="unpaid"
          title="Unpaid"
          description="Approved posts waiting for payment, per currency"
          action={
            <Link href="/admin/payouts" className="inline-flex items-center gap-1 text-[13px] text-muted-foreground hover:text-foreground">
              Payouts <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          }
          bodyClassName="px-4 py-4 sm:px-5"
        >
          <MoneyList rows={unpaidTotals()} figureClassName="text-[1.625rem] leading-tight" />
        </Panel>
        <Panel id="paid" title="Paid this month" description="November, per currency" bodyClassName="px-4 py-4 sm:px-5">
          <MoneyList rows={paidThisMonth()} figureClassName="text-[1.625rem] leading-tight" />
        </Panel>
      </div>

      <div className="mt-4">
        <ActivityChart />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Panel
          id="queue"
          title="Waiting for review"
          description="Oldest first. Each one takes a tap to approve."
          action={
            <Link href="/admin/review" className="inline-flex items-center gap-1 text-[13px] text-muted-foreground hover:text-foreground">
              Open queue <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          }
        >
          <ul className="divide-y">
            {queue.slice(0, 8).map((item) => (
              <ReviewRow key={`${item.campaign.id}-${item.creator.id}`} item={item} />
            ))}
          </ul>
          {queue.length > 8 ? (
            <p className="border-t px-5 py-3 text-[13px] text-muted-foreground">
              And {plural(queue.length - 8, "more item")} in the queue.
            </p>
          ) : null}
        </Panel>

        <Panel id="next" title="Coming up" description="Drops, windows and deadlines, in your time">
          <ol className="relative px-4 py-2 sm:px-5">
            {events.map((event, index) => {
              const client = clientById(event.campaign.clientId);
              const inMs = new Date(event.at).getTime() - nowMs;
              return (
                <li key={`${event.campaign.id}-${event.label}`} className="relative flex gap-3.5 py-2.5">
                  <span aria-hidden className="relative flex w-3 shrink-0 justify-center">
                    <span
                      className={cn(
                        "mt-1.5 size-2 rounded-full ring-4 ring-surface",
                        index === 0 ? "bg-foreground" : "bg-border-strong",
                      )}
                    />
                    {index < events.length - 1 ? (
                      <span className="absolute top-4 -bottom-3 w-px bg-border" />
                    ) : null}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="flex items-baseline justify-between gap-3">
                      <span className="truncate text-sm font-medium">{event.label}</span>
                      <span className="shrink-0 font-mono text-[11px] text-muted-foreground tabular">
                        in {formatCountdown(inMs)}
                      </span>
                    </p>
                    <p className="mt-0.5 flex min-w-0 items-center gap-1.5 text-[13px] text-muted-foreground">
                      <BrandTile initials={client?.initials ?? "?"} color={client?.color} size="xs" className="size-4 text-[7px]" />
                      <Link href={`/admin/campaigns/${event.campaign.id}`} className="truncate hover:text-foreground">
                        {event.campaign.title}
                      </Link>
                    </p>
                    <LocalWhen value={event.at} className="mt-0.5 block text-xs text-subtle-foreground" />
                  </div>
                </li>
              );
            })}
          </ol>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Panel
          id="in-flight"
          title="Campaigns in flight"
          description="Live, full and paused"
          action={
            <Link href="/admin/campaigns" className="inline-flex items-center gap-1 text-[13px] text-muted-foreground hover:text-foreground">
              All campaigns <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          }
        >
          <ul className="divide-y">
            {inFlight.map((campaign) => {
              const client = clientById(campaign.clientId);
              const stats = campaignStats(campaign);
              const filled = campaign.slots ? campaign.slotsTaken / campaign.slots : 0;
              return (
                <li key={campaign.id}>
                  <Link
                    href={`/admin/campaigns/${campaign.id}`}
                    className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-2/50 sm:px-5"
                  >
                    <BrandTile initials={client?.initials ?? "?"} color={client?.color} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{campaign.title}</p>
                      <div className="mt-1.5 flex items-center gap-2.5">
                        <div className="h-1 w-24 overflow-hidden rounded-full bg-surface-3 sm:w-36">
                          <div
                            className={cn("h-full rounded-full", filled >= 1 ? "bg-subtle-foreground" : "bg-foreground/70")}
                            style={{ width: `${Math.round(filled * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground tabular">
                          {campaign.slotsTaken}/{campaign.slots} slots
                        </span>
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1.5">
                      <StatusBadge kind="campaign" status={campaign.status} />
                      {stats.waiting ? (
                        <span className="text-xs text-muted-foreground tabular">{stats.waiting} to review</span>
                      ) : null}
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </Panel>

        <div className="grid gap-4">
          <Panel
            id="applications"
            title="New applications"
            action={
              <Link href="/admin/applications" className="text-[13px] text-muted-foreground hover:text-foreground">
                Review all
              </Link>
            }
          >
            <ul className="divide-y">
              {demoApplications.map((entry) => (
                <li key={entry.handle} className="flex items-center gap-3 px-4 py-2.5 sm:px-5">
                  <Avatar className="size-8">
                    <AvatarFallback className="text-[10px]">{brandInitials(entry.name)}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{entry.name}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {entry.handle} · {entry.niche}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground tabular">
                    {compact.format(entry.followers)} followers
                  </span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel
            id="leads"
            title="New leads"
            action={
              <Link href="/admin/leads" className="text-[13px] text-muted-foreground hover:text-foreground">
                Open leads
              </Link>
            }
          >
            <ul className="divide-y">
              {demoLeads.map((lead) => (
                <li key={lead.company} className="flex items-center gap-3 px-4 py-2.5 sm:px-5">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{lead.company}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {lead.contact} · {lead.launching}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">{lead.budget}</span>
                  <StatusBadge kind="lead" status="new" />
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <p className="mt-8 text-center text-xs text-subtle-foreground">
        Demo data, set on the afternoon of Nebula&apos;s launch day. Live numbers arrive with Milestones 5 to 9.
      </p>
    </>
  );
}
