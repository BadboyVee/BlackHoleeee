import Link from "next/link";
import { ArrowRight, Clock3 } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Countdown } from "@/components/ui/countdown";
import { LocalDateTime, UtcTime } from "@/components/ui/local-time";
import { formatMoney } from "@/lib/money";
import type { CampaignStatus } from "@/lib/statuses";
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

/** A campaign as creators see it on the board. */
function CampaignCard({ campaign, className }: { campaign: CampaignCardData; className?: string }) {
  const slotsLeft = Math.max(0, campaign.slots.total - campaign.slots.taken);
  const filled = campaign.slots.total ? campaign.slots.taken / campaign.slots.total : 1;

  return (
    <Card interactive className={cn("group overflow-hidden", className)}>
      {campaign.isNew ? (
        <div
          aria-hidden
          className="pointer-events-none absolute -top-16 -right-10 h-40 w-40 rounded-full bg-(--glow) blur-3xl"
        />
      ) : null}
      <div className="relative flex flex-col gap-5 p-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-xl border border-border-strong bg-surface-2 font-mono text-xs font-semibold">
              {campaign.brand.initials}
            </div>
            <p className="truncate text-sm font-medium text-muted-foreground">{campaign.brand.name}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {campaign.isNew ? <Badge variant="brand">New</Badge> : null}
            <StatusBadge kind="campaign" status={campaign.status} />
          </div>
        </div>

        <div className="-mt-1 flex flex-col gap-1.5">
          <h3 className="text-lg leading-snug font-semibold tracking-tight text-balance">{campaign.title}</h3>
          <p className="line-clamp-2 text-sm text-pretty text-muted-foreground">{campaign.summary}</p>
        </div>

        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-label text-subtle-foreground">Payout</p>
            <p className="mt-1 font-mono text-2xl font-semibold tracking-tight tabular">
              {formatMoney(campaign.payout.amount, campaign.payout.currency)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium tabular">
              {slotsLeft} of {campaign.slots.total} left
            </p>
            <div className="mt-2 h-1.5 w-28 overflow-hidden rounded-full bg-surface-3">
              <div
                className="h-full rounded-full bg-brand transition-[width] duration-700"
                style={{ width: `${Math.round(filled * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Badge variant="outline" className="gap-1.5">
            <XLogo className="size-3" />
            {campaign.deliverable}
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <Clock3 />
            Opens in <Countdown to={campaign.postWindow.start} className="text-foreground" />
          </Badge>
        </div>

        <div className="rounded-xl border bg-surface-2/50 px-3.5 py-3 text-sm">
          <p className="text-label text-subtle-foreground">Post window</p>
          <p className="mt-1.5 font-medium">
            <LocalDateTime value={campaign.postWindow.start} /> →{" "}
            <LocalDateTime value={campaign.postWindow.end} />
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            <UtcTime value={campaign.postWindow.start} /> to <UtcTime value={campaign.postWindow.end} />
          </p>
        </div>

        <Link
          href={campaign.href}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-primary text-sm font-medium text-primary-foreground transition-colors group-hover:bg-brand group-hover:text-brand-foreground"
        >
          {slotsLeft > 0 ? "View and claim" : "View campaign"}
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </Card>
  );
}

export { CampaignCard };
