"use client";

import { useMemo } from "react";
import Link from "next/link";
import { Wallet } from "lucide-react";
import { motion } from "motion/react";

import { StatusBadge } from "@/components/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { earningsFromClaims, earningsSummary } from "@/lib/campaigns/claims";
import { cn } from "@/lib/utils";

import { BrandTile } from "./brand-tile";
import { useClaims } from "./claim-store";
import { shortReference } from "./claim-row";
import { CopyButton } from "./copy-button";
import { useCampaignLookup } from "./creator-data";
import { useHydrated } from "./hooks";
import { Money } from "./money";
import { pressed, springArrive, stagger } from "./motion";
import { LocalWhen } from "./time";
import { displayType, panel } from "./ui";

function TotalCard({ label, hint, rows, index }: { label: string; hint: string; rows: { currency: string; amount: string }[]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...springArrive, delay: stagger(index, 0.06) }}
      className={cn(panel, "flex flex-col gap-2.5 p-4 sm:p-5")}
    >
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {rows.length ? (
        rows.map((row) => <Money key={row.currency} amount={row.amount} currency={row.currency} size="lg" />)
      ) : (
        <p className="text-figure text-[1.875rem] leading-none text-subtle-foreground">0</p>
      )}
      <p className="mt-auto pt-1 text-xs text-subtle-foreground">{hint}</p>
    </motion.div>
  );
}

/** What you've earned, per currency, and every payment with its reference. */
function CreatorEarnings() {
  const claims = useClaims();
  const lookup = useCampaignLookup();
  const hydrated = useHydrated();

  const { summary, rows } = useMemo(() => {
    const earnings = earningsFromClaims(claims.filter((claim) => lookup(claim.campaignId)));
    const sorted = [...earnings].sort((a, b) => {
      if (a.status !== b.status) return a.status === "unpaid" ? -1 : 1;
      return new Date(b.paidAt ?? 0).getTime() - new Date(a.paidAt ?? 0).getTime();
    });
    return { summary: earningsSummary(earnings), rows: sorted };
  }, [claims, lookup]);

  return (
    <div className="flex flex-col gap-6">
      <header className="pt-2 sm:pt-4">
        <h1 className="text-h2">Earnings</h1>
        <p className="mt-2 text-[15px] text-pretty text-muted-foreground sm:text-base">
          Approved posts earn as Unpaid, then turn Paid with a reference. Each currency is totalled on its own.
        </p>
      </header>

      {!hydrated ? (
        <div className="grid gap-3 sm:grid-cols-3">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-3">
          <TotalCard index={0} label="Unpaid" hint="Approved and on the way" rows={summary.unpaid} />
          <TotalCard index={1} label="Paid" hint="Sent, with a reference" rows={summary.paid} />
          <TotalCard index={2} label="Earned in total" hint="Never added across currencies" rows={summary.total} />
        </div>
      )}

      <section aria-labelledby="history">
        <h2 id="history" className={cn(displayType, "mb-3 text-[1.375rem] leading-none sm:text-[1.625rem]")}>
          History
        </h2>
        {!hydrated ? (
          <Skeleton className="h-48 rounded-2xl" />
        ) : rows.length === 0 ? (
          <div className={cn(panel, "flex flex-col items-center px-6 py-14 text-center shadow-none")}>
            <span className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground">
              <Wallet className="size-6" />
            </span>
            <p className={cn(displayType, "text-2xl leading-none")}>No earnings yet</p>
            <p className="mt-2 max-w-xs text-sm text-pretty text-muted-foreground">
              Once the agency approves your proof, the earning shows up here.
            </p>
          </div>
        ) : (
          <ul className={cn(panel, "divide-y overflow-hidden")}>
            {rows.map((row, index) => {
              const campaign = lookup(row.campaignId)!;
              return (
                <motion.li
                  key={row.campaignId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ ...springArrive, delay: stagger(index) }}
                  className="flex flex-wrap items-center gap-x-3.5 gap-y-2 p-4 sm:flex-nowrap sm:px-5"
                >
                  <BrandTile initials={campaign.brand.initials} color={campaign.brand.color} size="md" />
                  <motion.div whileTap={pressed} className="min-w-0 flex-1">
                    <Link href={`/dashboard/campaigns/${campaign.id}`} className="block min-w-0">
                      <p className="truncate text-[15px] font-semibold tracking-[-0.015em] hover:underline">{campaign.title}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {campaign.brand.name}
                        {row.paidAt ? (
                          <>
                            {" · paid "}
                            <LocalWhen value={row.paidAt} />
                          </>
                        ) : (
                          " · waiting to be paid"
                        )}
                      </p>
                    </Link>
                  </motion.div>
                  <div className="flex shrink-0 items-center gap-2.5">
                    <Money amount={row.amount} currency={row.currency} size="md" />
                    <StatusBadge kind="earning" status={row.status} />
                  </div>
                  {row.reference ? (
                    <div className="flex w-full items-center justify-between gap-3 rounded-xl bg-surface-2/60 py-1 pr-1 pl-3 sm:w-auto sm:bg-transparent sm:p-0">
                      <span className="font-mono text-xs text-muted-foreground">ref {shortReference(row.reference)}</span>
                      <CopyButton value={row.reference} label="Copy payment reference" iconOnly toastMessage="Reference copied" />
                    </div>
                  ) : null}
                </motion.li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}

export { CreatorEarnings };
