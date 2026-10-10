import type { Metadata } from "next";
import Link from "next/link";
import { AlertTriangle, ArrowRight, Check } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { SampleBadge } from "@/components/sample-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { splitMoney } from "@/lib/money";
import {
  sampleAdminStats,
  sampleLiveCampaigns,
  sampleMoney,
  sampleReviewQueue,
} from "@/lib/sample-data";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: "Overview" };

function MoneyList({ rows }: { rows: { amount: string; currency: string }[] }) {
  return (
    <div className="mt-3 flex flex-col gap-1.5">
      {rows.map((row) => {
        const money = splitMoney(row.amount, row.currency);
        return (
          <p key={row.currency} className="flex items-baseline gap-1">
            <span className="text-figure text-2xl leading-none">
              {money.value}
            </span>
            {money.unit ? <span className="text-xs text-muted-foreground">{money.unit}</span> : null}
          </p>
        );
      })}
    </div>
  );
}

export default function AdminOverviewPage() {
  return (
    <>
      <PageHeader
        eyebrow={<SampleBadge milestone={9} />}
        title="Overview"
        description="Seven items are waiting for review and twelve posts are due today."
        actions={
          <Button asChild size="sm">
            <Link href="/admin/campaigns">
              New campaign
              <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {sampleAdminStats.map((stat) => (
          <Card key={stat.label} className={cn("p-5", stat.highlight && "border-border-strong")}>
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            <p className="mt-3 text-figure text-[2rem] leading-none">
              {stat.value}
            </p>
          </Card>
        ))}
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">Unpaid, by currency</p>
          <MoneyList rows={sampleMoney.unpaid} />
        </Card>
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">Paid this month</p>
          <MoneyList rows={sampleMoney.paidThisMonth} />
        </Card>
      </div>

      <div className="mt-10 grid gap-8 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <section aria-labelledby="review" className="min-w-0">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="review" className="text-sm font-semibold">
              Waiting for review
            </h2>
            <Link
              href="/admin/review"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Open queue
              <ArrowRight className="size-3.5" />
            </Link>
          </div>
          <Card className="divide-y">
            {sampleReviewQueue.map((item) => (
              <div key={`${item.creator.handle}-${item.campaign}`} className="flex items-start gap-3.5 px-5 py-4">
                <span
                  aria-hidden
                  className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
                  style={{
                    background: `linear-gradient(140deg, hsl(${item.creator.hue} 32% 58%), hsl(${item.creator.hue + 30} 30% 28%))`,
                  }}
                >
                  {item.creator.initials}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[15px] font-medium tracking-[-0.015em]">
                    {item.type} · {item.creator.name}
                  </p>
                  <p className="truncate text-sm text-muted-foreground">
                    {item.campaign} · waiting {item.waiting}
                  </p>
                  {item.checks.length ? (
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {item.checks.map((check) => (
                        <span
                          key={check.label}
                          data-tone={check.ok ? "green" : "amber"}
                          className="inline-flex items-center gap-1 rounded-full border bg-surface-2/60 px-2 py-0.5 text-xs text-muted-foreground"
                        >
                          {check.ok ? (
                            <Check className="size-3 text-(--tone-fg)" strokeWidth={2.5} />
                          ) : (
                            <AlertTriangle className="size-3 text-(--tone-fg)" />
                          )}
                          {check.label}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
                <Button asChild variant="secondary" size="sm" className="shrink-0">
                  <Link href="/admin/review">Review</Link>
                </Button>
              </div>
            ))}
          </Card>
        </section>

        <section aria-labelledby="live" className="min-w-0">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="live" className="text-sm font-semibold">
              Live campaigns
            </h2>
            <Link
              href="/admin/campaigns"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              All campaigns
              <ArrowRight className="size-3.5" />
            </Link>
          </div>
          <Card className="divide-y">
            {sampleLiveCampaigns.map((campaign) => (
              <div key={campaign.title} className="px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-[15px] font-medium tracking-[-0.015em]">{campaign.title}</p>
                    <p className="truncate text-sm text-muted-foreground">{campaign.brand}</p>
                  </div>
                  <StatusBadge kind="campaign" status={campaign.status} />
                </div>
                <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-surface-3">
                    <div
                      className="h-full rounded-full bg-foreground/70"
                      style={{ width: `${Math.round((campaign.taken / campaign.total) * 100)}%` }}
                    />
                  </div>
                  <span className="tabular">
                    {campaign.taken}/{campaign.total} claimed · {campaign.posted} posted
                  </span>
                </div>
              </div>
            ))}
          </Card>
        </section>
      </div>
    </>
  );
}
