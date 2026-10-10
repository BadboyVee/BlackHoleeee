import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ChevronRight } from "lucide-react";

import { CampaignCard } from "@/components/campaign/campaign-card";
import { PageHeader } from "@/components/layout/page-header";
import { SampleBadge } from "@/components/sample-badge";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Countdown } from "@/components/ui/countdown";
import { splitMoney } from "@/lib/money";
import { sampleCampaigns, sampleCreatorActions, sampleEarnings } from "@/lib/sample-data";

export const metadata: Metadata = { title: "Home" };

function Amount({ amount, currency, size = "lg" }: { amount: string; currency: string; size?: "lg" | "sm" }) {
  const money = splitMoney(amount, currency);
  return (
    <span className="inline-flex items-baseline gap-1">
      <span
        className={
          size === "lg"
            ? "text-figure text-[1.75rem] leading-none"
            : "text-figure text-base"
        }
      >
        {money.value}
      </span>
      {money.unit ? <span className="text-xs text-muted-foreground">{money.unit}</span> : null}
    </span>
  );
}

export default function CreatorHomePage() {
  return (
    <>
      <PageHeader
        eyebrow={<SampleBadge milestone={5} />}
        title="Welcome back"
        description="Two things need you, and two new campaigns just dropped."
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="flex min-w-0 flex-col gap-10">
          <section aria-labelledby="needs-you">
            <h2 id="needs-you" className="mb-3 text-sm font-semibold">
              Needs you
            </h2>
            <Card className="divide-y">
              {sampleCreatorActions.map((action) => (
                <Link
                  key={action.campaign}
                  href="/dashboard/my-campaigns"
                  className="group flex items-center gap-4 px-5 py-4 transition-colors first:rounded-t-2xl last:rounded-b-2xl hover:bg-surface-2/60"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge kind="claim" status={action.status} />
                      <span className="text-xs text-subtle-foreground">{action.brand}</span>
                    </div>
                    <p className="mt-2 text-[15px] leading-snug font-medium tracking-[-0.015em] text-pretty">
                      {action.kind}: {action.campaign}
                    </p>
                    <p className="mt-1 line-clamp-2 text-sm text-pretty text-muted-foreground">{action.detail}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-xs text-subtle-foreground">Due in</p>
                    <Countdown to={action.due} className="font-mono text-[13px] font-medium" />
                  </div>
                  <ChevronRight className="hidden size-4 shrink-0 text-subtle-foreground transition-transform group-hover:translate-x-0.5 sm:block" />
                </Link>
              ))}
            </Card>
          </section>

          <section aria-labelledby="new-drops">
            <div className="mb-3 flex items-center justify-between">
              <h2 id="new-drops" className="text-sm font-semibold">
                New drops
              </h2>
              <Link
                href="/dashboard/campaigns"
                className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                All campaigns
                <ArrowRight className="size-3.5" />
              </Link>
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              {sampleCampaigns
                .filter((campaign) => campaign.isNew)
                .map((campaign) => (
                  <CampaignCard key={campaign.title} campaign={campaign} />
                ))}
            </div>
          </section>
        </div>

        <aside className="flex flex-col gap-4">
          <h2 className="sr-only">Earnings</h2>
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">Unpaid</p>
            <div className="mt-3 flex flex-col gap-2">
              {sampleEarnings.unpaid.map((row) => (
                <Amount key={row.currency} amount={row.amount} currency={row.currency} />
              ))}
            </div>
            <div className="mt-5 border-t pt-4">
              <p className="text-sm text-muted-foreground">Paid this month</p>
              <div className="mt-2">
                {sampleEarnings.paidThisMonth.map((row) => (
                  <Amount key={row.currency} amount={row.amount} currency={row.currency} size="sm" />
                ))}
              </div>
            </div>
            <Link
              href="/dashboard/earnings"
              className="mt-5 inline-flex items-center gap-1 text-sm font-medium transition-colors hover:text-muted-foreground"
            >
              View earnings
              <ArrowRight className="size-3.5" />
            </Link>
          </Card>
          <Card className="p-5">
            <p className="text-sm font-medium">Totals stay per currency</p>
            <p className="mt-1.5 text-sm text-pretty text-muted-foreground">
              USD, USDC and NGN are never added together, so every number means exactly what it says.
            </p>
          </Card>
        </aside>
      </div>
    </>
  );
}
