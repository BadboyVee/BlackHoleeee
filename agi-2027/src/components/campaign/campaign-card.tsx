import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Countdown } from "@/components/ui/countdown";
import { LocalTimeRange } from "@/components/ui/local-time";
import { splitMoney } from "@/lib/money";
import type { CampaignStatus } from "@/lib/statuses";
import { formatUtcTime } from "@/lib/time";
import { cn } from "@/lib/utils";

export type CampaignCardData = {
  href: string;
  brand: { name: string; initials: string };
  title: string;
  summary: string;
  payout: { amount: string; currency: string };
  slots: { total: number; taken: number };
  platform: "x";
  deliverable: string;
  postWindow: { start: string; end: string };
  status: CampaignStatus;
  isNew?: boolean;
};

/** A campaign as creators see it on the board. The whole card opens the campaign. */
function CampaignCard({ campaign, className }: { campaign: CampaignCardData; className?: string }) {
  const slotsLeft = Math.max(0, campaign.slots.total - campaign.slots.taken);
  const filled = campaign.slots.total ? campaign.slots.taken / campaign.slots.total : 1;
  const payout = splitMoney(campaign.payout.amount, campaign.payout.currency);

  return (
    <Card interactive className={cn("group", className)}>
      <div className="flex flex-col gap-5 p-5">
        <div className="flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-[10px] border bg-surface-2 font-mono text-[11px] font-semibold tracking-tight">
            {campaign.brand.initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{campaign.brand.name}</p>
            <p className="truncate text-xs text-subtle-foreground">{campaign.deliverable} on X</p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {campaign.isNew ? <Badge variant="brand">New</Badge> : null}
            <StatusBadge kind="campaign" status={campaign.status} />
          </div>
        </div>

        <div>
          <h3 className="flex items-start gap-2 text-[17px] leading-snug font-semibold tracking-[-0.022em]">
            <Link href={campaign.href} className="after:absolute after:inset-0 after:rounded-2xl">
              {campaign.title}
            </Link>
            <ArrowUpRight
              aria-hidden
              className="mt-0.5 size-4 shrink-0 text-subtle-foreground opacity-0 transition-[opacity,transform] duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100"
            />
          </h3>
          <p className="mt-1.5 line-clamp-2 text-sm text-pretty text-muted-foreground">{campaign.summary}</p>
        </div>

        <div className="flex items-end justify-between gap-4 border-t pt-4">
          <div>
            <p className="text-xs text-subtle-foreground">Payout per post</p>
            <p className="mt-1.5 flex items-baseline gap-1.5">
              <span className="text-figure text-2xl leading-none">
                {payout.value}
              </span>
              {payout.unit ? <span className="text-sm text-muted-foreground">{payout.unit}</span> : null}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm tabular">
              <span className="font-medium">{slotsLeft}</span>
              <span className="text-muted-foreground"> of {campaign.slots.total} slots left</span>
            </p>
            <div className="mt-2 ml-auto h-1 w-28 overflow-hidden rounded-full bg-surface-3">
              <div
                className={cn("h-full rounded-full", slotsLeft === 0 ? "bg-subtle-foreground" : "bg-foreground/70")}
                style={{ width: `${Math.round(filled * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-end justify-between gap-3 text-[13px]">
          <div className="min-w-0">
            <LocalTimeRange
              start={campaign.postWindow.start}
              end={campaign.postWindow.end}
              className="block truncate text-foreground/90"
            />
            <span className="mt-0.5 block text-xs text-subtle-foreground">
              {formatUtcTime(campaign.postWindow.start)} to {formatUtcTime(campaign.postWindow.end)}
            </span>
          </div>
          <span className="shrink-0 text-right text-xs text-muted-foreground">
            Opens in
            <Countdown
              to={campaign.postWindow.start}
              className="mt-0.5 block font-mono text-[13px] font-medium text-foreground"
            />
          </span>
        </div>
      </div>
    </Card>
  );
}

export { CampaignCard };
