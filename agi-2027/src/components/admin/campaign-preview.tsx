"use client";

import { Check, FileText, Link2, Quote, Users } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import {
  claimModeMeta,
  deliverableMeta,
  NEEDS_TARGET_POST,
  platformLabel,
  type ClaimMode,
  type Deliverable,
  type Platform,
} from "@/lib/campaigns/options";
import type { DemoCampaign, DemoClient } from "@/lib/campaigns/demo";
import { splitMoney } from "@/lib/money";
import type { CampaignStatus } from "@/lib/statuses";
import { formatCountdown } from "@/lib/time";
import { cn } from "@/lib/utils";
import { BrandTile } from "./brand-tile";
import { PlatformIcon } from "./platform-icon";
import { LocalWindow, useNowMinute, utcWindowText } from "./time-text";

/** Everything a creator sees about a campaign, from either the builder or a saved campaign. */
export type PreviewModel = {
  brand: { name: string; initials: string; color?: string };
  title: string;
  summary: string;
  platform: Platform;
  deliverable: Deliverable;
  /** Null while the amount isn't valid yet. */
  payout: { amount: string; currency: string } | null;
  customRates: boolean;
  slots: number | null;
  slotsTaken: number;
  window: { start: string; end: string } | null;
  claimMode: ClaimMode;
  draftRequired: boolean;
  paidLabelRequired: boolean;
  status: CampaignStatus;
  isNew: boolean;
  brief: { about: string; whatToSay: string; keyMessage: string; dos: string[]; donts: string[] };
  angles: string[];
  requiredTags: { mentions: string[]; hashtags: string[]; keywords: string[] };
  links: { targetPostUrl: string; trackingUrl: string };
  assets: { files: number; brandKit: boolean };
};

export function previewFromCampaign(campaign: DemoCampaign, client: DemoClient | undefined): PreviewModel {
  return {
    brand: { name: client?.name ?? "Brand", initials: client?.initials ?? "?", color: client?.color },
    title: campaign.title,
    summary: campaign.summary,
    platform: campaign.platform,
    deliverable: campaign.deliverable,
    payout: campaign.payout,
    customRates: campaign.tierPayouts.length + campaign.creatorPayouts.length > 0,
    slots: campaign.slots,
    slotsTaken: campaign.slotsTaken,
    window: { start: campaign.timing.postWindowStart, end: campaign.timing.postWindowEnd },
    claimMode: campaign.claimMode,
    draftRequired: campaign.draftRequired,
    paidLabelRequired: campaign.paidLabelRequired,
    status: campaign.status,
    isNew: false,
    brief: campaign.brief,
    angles: campaign.angles,
    requiredTags: campaign.requiredTags,
    links: campaign.links,
    assets: { files: campaign.assets.files.length, brandKit: Boolean(campaign.assets.brandKitUrl) },
  };
}

/** "nebula.example/launch" from a full link, for compact display. */
export function shortLink(url: string) {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname === "/" ? "" : parsed.pathname;
    return `${parsed.host.replace(/^www\./, "")}${path}${parsed.search}`;
  } catch {
    return url;
  }
}

function Placeholder({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("text-subtle-foreground italic", className)}>{children}</span>;
}

/** The campaign as a card on the creator board. */
export function CreatorCardPreview({ model, className }: { model: PreviewModel; className?: string }) {
  const now = useNowMinute();
  const payout = model.payout ? splitMoney(model.payout.amount, model.payout.currency) : null;
  const slots = model.slots && model.slots > 0 ? model.slots : null;
  const left = slots ? Math.max(0, slots - model.slotsTaken) : null;
  const filled = slots ? Math.min(1, model.slotsTaken / slots) : 0;
  const opensIn = model.window && now !== null ? new Date(model.window.start).getTime() - now : null;

  return (
    <article
      aria-label="Campaign card preview"
      className={cn("relative overflow-hidden rounded-2xl border bg-surface shadow-soft", className)}
    >
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center gap-3">
          <BrandTile initials={model.brand.initials || "?"} color={model.brand.color} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{model.brand.name || <Placeholder>Brand</Placeholder>}</p>
            <p className="flex items-center gap-1 truncate text-xs text-subtle-foreground">
              <PlatformIcon platform={model.platform} className="size-3" />
              {deliverableMeta[model.deliverable].label} on {platformLabel[model.platform]}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {model.isNew ? <Badge variant="brand">New</Badge> : null}
            <StatusBadge kind="campaign" status={model.status} />
          </div>
        </div>

        <div>
          <h3 className="text-[17px] leading-snug font-semibold tracking-[-0.022em] text-pretty">
            {model.title.trim() || <Placeholder>Your campaign title</Placeholder>}
          </h3>
          <p className="mt-1.5 line-clamp-2 text-sm text-pretty text-muted-foreground">
            {model.summary.trim() || <Placeholder>One line on what creators will post.</Placeholder>}
          </p>
        </div>

        <div className="flex items-end justify-between gap-4 border-t pt-4">
          <div className="min-w-0">
            <p className="text-xs text-subtle-foreground">{model.customRates ? "Base payout per post" : "Payout per post"}</p>
            {payout ? (
              <p className="mt-1.5 flex items-baseline gap-1.5">
                <span className="text-figure text-2xl leading-none">{payout.value}</span>
                {payout.unit ? <span className="text-sm text-muted-foreground">{payout.unit}</span> : null}
              </p>
            ) : (
              <p className="mt-1.5 text-sm">
                <Placeholder>Set a payout</Placeholder>
              </p>
            )}
            {model.customRates && payout ? <p className="mt-1 text-[11px] text-muted-foreground">Rates vary by tier or creator</p> : null}
          </div>
          <div className="text-right">
            <p className="text-sm tabular">
              {left !== null && slots !== null ? (
                <>
                  <span className="font-medium">{left}</span>
                  <span className="text-muted-foreground"> of {slots} slots left</span>
                </>
              ) : (
                <Placeholder>Slots</Placeholder>
              )}
            </p>
            <div className="mt-2 ml-auto h-1 w-24 overflow-hidden rounded-full bg-surface-3">
              <div
                className={cn("h-full rounded-full", left === 0 ? "bg-subtle-foreground" : "bg-foreground/70")}
                style={{ width: `${Math.round(filled * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-end justify-between gap-3 text-[13px]">
          <div className="min-w-0">
            {model.window ? (
              <>
                <LocalWindow start={model.window.start} end={model.window.end} className="block truncate text-foreground/90" />
                <span className="mt-0.5 block truncate text-xs text-subtle-foreground">
                  {utcWindowText(model.window.start, model.window.end)}
                </span>
              </>
            ) : (
              <Placeholder>Pick the post window</Placeholder>
            )}
          </div>
          {opensIn !== null && opensIn > 0 ? (
            <span className="shrink-0 text-right text-xs text-muted-foreground">
              Opens in
              <span className="mt-0.5 block font-mono text-[13px] font-medium text-foreground tabular">{formatCountdown(opensIn)}</span>
            </span>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline">{model.claimMode === "instant" ? "Instant claim" : "Apply to join"}</Badge>
          {model.draftRequired ? <Badge variant="outline">Draft first</Badge> : null}
          {model.paidLabelRequired ? <Badge variant="outline">Paid partnership label</Badge> : null}
        </div>
      </div>
    </article>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <p className="text-label text-subtle-foreground">{label}</p>
      <div className="text-[13px] leading-relaxed">{children}</div>
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex h-6 items-center rounded-full border bg-surface-2/60 px-2 font-mono text-[11px] text-foreground">
      {children}
    </span>
  );
}

/** The brief as a creator reads it after opening the card, kept compact. */
export function BriefPreview({ model, className }: { model: PreviewModel; className?: string }) {
  const tags = [...model.requiredTags.mentions, ...model.requiredTags.hashtags];
  const needsTarget = NEEDS_TARGET_POST.has(model.deliverable);
  return (
    <div className={cn("grid gap-4 rounded-2xl border bg-surface p-4", className)}>
      <Section label="Key message">
        {model.brief.keyMessage.trim() ? (
          <p className="flex gap-2 text-[14px] font-medium text-pretty">
            <Quote className="mt-1 size-3.5 shrink-0 text-subtle-foreground" aria-hidden />
            {model.brief.keyMessage}
          </p>
        ) : (
          <Placeholder>The one message every post must land.</Placeholder>
        )}
      </Section>

      <Section label="What to post">
        {model.brief.whatToSay.trim() ? (
          <p className="line-clamp-5 text-pretty text-muted-foreground">{model.brief.whatToSay}</p>
        ) : (
          <Placeholder>What the post should say.</Placeholder>
        )}
      </Section>

      {needsTarget ? (
        <Section label={model.deliverable === "quote" ? "Quote this post" : "Reply to this post"}>
          {model.links.targetPostUrl ? (
            <p className="flex min-w-0 items-center gap-1.5 text-muted-foreground">
              <Link2 className="size-3.5 shrink-0" aria-hidden />
              <span className="truncate">{shortLink(model.links.targetPostUrl)}</span>
            </p>
          ) : (
            <Placeholder>The post to {model.deliverable === "quote" ? "quote" : "reply to"}.</Placeholder>
          )}
        </Section>
      ) : null}

      {tags.length || model.requiredTags.keywords.length || model.links.trackingUrl ? (
        <Section label="Must include">
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <Chip key={tag}>{tag}</Chip>
            ))}
            {model.requiredTags.keywords.map((keyword) => (
              <Chip key={keyword}>&ldquo;{keyword}&rdquo;</Chip>
            ))}
          </div>
          {model.links.trackingUrl ? (
            <p className="mt-2 flex min-w-0 items-center gap-1.5 text-muted-foreground">
              <Link2 className="size-3.5 shrink-0" aria-hidden />
              <span className="truncate">{shortLink(model.links.trackingUrl)}</span>
            </p>
          ) : null}
        </Section>
      ) : null}

      {model.angles.length ? (
        <Section label="Your angle">
          <p className="text-muted-foreground">
            You&apos;ll get one of {model.angles.length} {model.angles.length === 1 ? "angle" : "angles"}, like{" "}
            <span className="text-foreground">&ldquo;{model.angles[0]}&rdquo;</span>.
          </p>
        </Section>
      ) : null}

      {model.brief.dos.length || model.brief.donts.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {model.brief.dos.length ? (
            <Section label="Do">
              <ul className="grid gap-1">
                {model.brief.dos.slice(0, 3).map((item) => (
                  <li key={item} className="flex gap-1.5 text-muted-foreground">
                    <Check className="mt-1 size-3 shrink-0 text-(--tone-green)" aria-hidden data-tone="green" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}
          {model.brief.donts.length ? (
            <Section label="Don't">
              <ul className="grid gap-1">
                {model.brief.donts.slice(0, 3).map((item) => (
                  <li key={item} className="flex gap-1.5 text-muted-foreground">
                    <span aria-hidden className="mt-2 h-px w-2.5 shrink-0 bg-destructive-text" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-x-4 gap-y-1.5 border-t pt-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <FileText className="size-3.5" aria-hidden />
          {model.assets.files
            ? `${model.assets.files} ${model.assets.files === 1 ? "file" : "files"}${model.assets.brandKit ? " and a brand kit" : ""}`
            : model.assets.brandKit
              ? "Brand kit"
              : "No assets"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Users className="size-3.5" aria-hidden />
          {claimModeMeta[model.claimMode].label} claim
        </span>
      </div>
    </div>
  );
}
