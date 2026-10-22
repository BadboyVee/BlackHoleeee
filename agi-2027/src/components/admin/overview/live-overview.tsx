import Link from "next/link";
import { ArrowUpRight, Megaphone } from "lucide-react";

import { Panel } from "@/components/admin/panel";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { LocalDateTime } from "@/components/ui/local-time";
import { Skeleton } from "@/components/ui/skeleton";
import { initialsFor } from "@/lib/auth/account-display";
import { listApplications, listSignupsWithoutApplication } from "@/lib/creators/queries";

import { oldestWaiting, overviewCounts } from "./live-counts";

/*
 * The overview on the live site: only what's real today. Applications and
 * sign ups come from the database through the staff member's own session.
 * Campaigns aren't built yet, so that panel says so plainly.
 */

type Tile = { label: string; value: number; detail: string; href: string; attention?: boolean };

function Tiles({ items }: { items: Tile[] }) {
  return (
    <div className="grid grid-cols-1 overflow-hidden rounded-lg border bg-border shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)] [gap:1px] sm:grid-cols-3">
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

export async function LiveOverview() {
  const [rows, signups] = await Promise.all([listApplications(), listSignupsWithoutApplication()]);
  const applications = rows ?? [];
  const counts = overviewCounts(applications, signups ?? []);
  const waiting = oldestWaiting(applications);

  const tiles: Tile[] = [
    {
      label: "Waiting for review",
      value: counts.waiting,
      detail: counts.waiting ? "Applications to approve or reject." : "You're all caught up.",
      href: "/admin/applications",
      attention: true,
    },
    {
      label: "Approved creators",
      value: counts.approved,
      detail: "Accepted through an application or an invite.",
      href: "/admin/applications?status=approved",
    },
    {
      label: "Not applied yet",
      value: counts.notApplied,
      detail: "Made an account but haven't sent the form.",
      href: "/admin/applications?status=not-applied",
    },
  ];

  return (
    <>
      <Tiles items={tiles} />

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <Panel
          id="overview-waiting"
          title="Waiting for review"
          description="Oldest first, so nobody waits too long."
          action={
            <Link href="/admin/applications" className="text-[13px] text-muted-foreground hover:text-foreground">
              Review all
            </Link>
          }
        >
          {waiting.length ? (
            <ul className="divide-y">
              {waiting.map((row) => (
                <li key={row.id}>
                  <Link
                    href="/admin/applications"
                    className="flex min-h-14 items-center gap-3 px-4 py-2.5 transition-colors hover:bg-surface-2/50 sm:px-5"
                  >
                    <Avatar className="size-8">
                      <AvatarFallback className="text-[10px]">{initialsFor(row.applicant.displayName)}</AvatarFallback>
                    </Avatar>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">{row.applicant.displayName || "No name given"}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {row.applicant.xHandle ? `@${row.applicant.xHandle} · ` : ""}Applied <LocalDateTime value={row.createdAt} />
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-4 py-6 text-sm text-muted-foreground sm:px-5">No applications waiting.</p>
          )}
        </Panel>

        <Panel id="overview-campaigns" title="Campaigns">
          <EmptyState
            icon={Megaphone}
            title="No campaigns yet"
            description="Campaigns you run will show here."
            className="rounded-none border-0 bg-transparent py-10 sm:py-12"
          />
        </Panel>
      </div>
    </>
  );
}

/** Shown for a moment while the numbers stream in. */
export function LiveOverviewSkeleton() {
  return (
    <div role="status" className="grid gap-4">
      <span className="sr-only">Loading the overview</span>
      <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border sm:grid-cols-3">
        {[0, 1, 2].map((tile) => (
          <div key={tile} className="grid min-h-[7.25rem] content-between bg-surface p-4 sm:p-5">
            <Skeleton className="h-3.5 w-28" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-3 w-40 max-w-full" />
          </div>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-56 rounded-lg" />
        <Skeleton className="h-56 rounded-lg" />
      </div>
    </div>
  );
}
