import type { CSSProperties } from "react";
import Link from "next/link";
import { ArrowRight, Lock, Send, Zap } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { BrandTile, inkOn } from "@/components/creator/brand-tile";
import { StatusDot } from "@/components/status-badge";
import { LocalTimeRange } from "@/components/ui/local-time";
import { publicCampaignSignupHref, type PublicCampaign } from "@/lib/campaigns/public";
import { deliverableMeta, platformLabel } from "@/lib/campaigns/options";
import { campaignStatusMeta } from "@/lib/statuses";
import { formatDateTime, formatTime, formatUtcTime } from "@/lib/time";
import { cn } from "@/lib/utils";

/** "16:00 to 20:00 UTC", or both days when the window runs past midnight UTC. */
function utcWindow(start: string, end: string): string {
  const from = formatDateTime(start, "UTC");
  const to = formatDateTime(end, "UTC");
  const day = (formatted: string) => formatted.slice(0, formatted.lastIndexOf(","));
  return day(from) === day(to) ? `${formatTime(start, "UTC")} to ${formatUtcTime(end)}` : `${from} to ${to} UTC`;
}

/**
 * A campaign on the public board: who it's for, what to post, when, and how
 * many slots are left. The payout stays hidden; the button sends people to
 * sign up and then straight to this campaign. Each look dresses it its own
 * way: Renaissance is an editorial entry with hairlines, Agent a soft card with
 * warm red accents, Drop a juicy block in the brand's own color.
 */
function PublicCampaignCard({ campaign, index }: { campaign: PublicCampaign; index: number }) {
  const full = campaign.status === "full";
  const left = Math.max(0, campaign.slots.total - campaign.slots.taken);
  const share = campaign.slots.total > 0 ? campaign.slots.taken / campaign.slots.total : 1;
  const status = campaignStatusMeta[campaign.status];
  const deliverable = deliverableMeta[campaign.deliverable].label;
  const platform = platformLabel[campaign.platform];
  const titleId = `campaign-${campaign.id}`;
  // The client's color comes from data, so it travels as variables the look can use.
  const brandVars = {
    "--campaign-color": campaign.brand.color,
    "--campaign-ink": inkOn(campaign.brand.color),
  } as CSSProperties;

  return (
    <article
      aria-labelledby={titleId}
      style={brandVars}
      className={cn(
        "group relative isolate flex h-full flex-col overflow-hidden border bg-surface",
        "transition-[transform,box-shadow,border-color] duration-300 ease-snap motion-reduce:transition-none",
        // Renaissance: an editorial entry, hairline frame and small radius.
        "renaissance:rounded-[var(--radius-sm)] renaissance:border-border-strong renaissance:bg-surface/70",
        // Agent: soft and round, lifts on hover.
        "agent:rounded-[1.75rem] agent:border-transparent agent:shadow-soft agent:ring-1 agent:ring-border agent:hover:-translate-y-1 agent:hover:shadow-float",
        // Drop: a juicy brand block on top of a plain card.
        "drop:rounded-[1.75rem] drop:border-transparent drop:shadow-soft drop:hover:-translate-y-1.5 drop:hover:shadow-float",
      )}
    >
      {/* Brand and title. In Drop this whole block takes the client's color. */}
      <div
        className={cn(
          "relative px-5 pt-5 sm:px-6 sm:pt-6",
          "renaissance:border-b renaissance:border-border renaissance:pb-5",
          "drop:overflow-hidden drop:bg-(--campaign-color) drop:pb-6 drop:text-(--campaign-ink)",
          // A full campaign keeps its color, a little quieter.
          full && "drop:saturate-[0.55]",
        )}
      >
        {/* Drop: the client's initials, huge and faint, bleeding off the corner. */}
        <span
          aria-hidden
          className="pointer-events-none absolute -top-3 -right-2 hidden font-[family-name:var(--font-anton)] text-[7.5rem] leading-none opacity-20 transition-transform duration-500 ease-snap select-none group-hover:-translate-x-1 group-hover:translate-y-1 drop:block motion-reduce:transition-none"
        >
          {campaign.brand.initials}
        </span>

        <div className="relative flex items-center gap-3">
          <BrandTile
            initials={campaign.brand.initials}
            color={campaign.brand.color}
            size="sm"
            className={cn("drop:hidden", full && "saturate-50")}
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold tracking-[-0.01em] drop:text-[15px]">{campaign.brand.name}</p>
            <p className="font-mono text-[11px] tracking-[0.06em] text-muted-foreground uppercase renaissance:block agent:hidden drop:hidden">
              No. {String(index + 1).padStart(2, "0")}
            </p>
          </div>
          <span
            className={cn(
              "inline-flex h-7 shrink-0 items-center gap-1.5 rounded-full px-2.5 text-xs font-semibold",
              "bg-surface-2 ring-1 ring-border",
              "renaissance:rounded-[var(--radius-sm)] renaissance:bg-transparent renaissance:font-mono renaissance:text-[11px] renaissance:tracking-[0.06em] renaissance:uppercase",
              // Drop: an inverted pill, so the label keeps full contrast on any brand color.
              "drop:bg-(--campaign-ink) drop:text-(--campaign-color) drop:ring-0",
            )}
          >
            <StatusDot tone={status.tone} pulse={status.pulse} className="drop:text-current" />
            {status.label}
          </span>
        </div>

        <h3
          id={titleId}
          className={cn(
            "relative mt-4 text-[1.1875rem] leading-snug font-semibold tracking-[-0.022em] text-balance",
            "renaissance:mt-5 renaissance:text-[1.5rem] renaissance:leading-[1.1] renaissance:font-bold renaissance:tracking-[-0.04em]",
            "agent:font-medium agent:tracking-[-0.03em]",
            "drop:mt-10 drop:max-w-[14ch] drop:font-[family-name:var(--font-anton)] drop:text-[2.125rem] drop:leading-[0.98] drop:font-normal drop:tracking-[0.01em] drop:uppercase",
          )}
        >
          {campaign.title}
        </h3>
      </div>

      <div className="relative flex flex-1 flex-col gap-5 px-5 pt-4 pb-5 sm:px-6 sm:pb-6 drop:pt-5">
        <p className="text-[15px] leading-relaxed text-pretty text-muted-foreground">{campaign.summary}</p>

        <ul className="flex flex-wrap gap-1.5" aria-label="What to post">
          <li className={chip}>
            {campaign.platform === "x" ? <XLogo className="size-3" /> : null}
            {campaign.platform === "x" ? deliverable : `${deliverable} on ${platform}`}
          </li>
          <li className={chip}>
            {campaign.claimMode === "instant" ? <Zap aria-hidden /> : <Send aria-hidden />}
            {campaign.claimMode === "instant" ? "Instant claim" : "Apply to join"}
          </li>
        </ul>

        <dl
          className={cn(
            "mt-auto grid gap-3 text-sm",
            "agent:rounded-[1.25rem] agent:bg-surface-2/70 agent:p-4",
            "renaissance:gap-0 renaissance:divide-y renaissance:divide-border renaissance:border-y renaissance:border-border",
          )}
        >
          <div className="renaissance:py-3">
            <dt className={label}>Post window</dt>
            <dd className="mt-1">
              <LocalTimeRange
                start={campaign.postWindow.start}
                end={campaign.postWindow.end}
                className="block font-medium"
              />
              <span className="block text-xs text-muted-foreground">
                {utcWindow(campaign.postWindow.start, campaign.postWindow.end)}
              </span>
            </dd>
          </div>

          <div className="renaissance:py-3">
            <dt className={label}>Slots</dt>
            <dd className="mt-1.5">
              <span className="flex items-baseline justify-between gap-3">
                {full ? (
                  <span className="font-semibold">All {campaign.slots.total} taken</span>
                ) : (
                  <span>
                    <span className="font-semibold tabular-nums">{left}</span>
                    <span className="text-muted-foreground"> of {campaign.slots.total} left</span>
                  </span>
                )}
              </span>
              <span aria-hidden className="mt-2 block h-1.5 overflow-hidden rounded-full bg-surface-3">
                <span
                  className={cn(
                    "block h-full origin-left rounded-full bg-foreground/80 transition-transform duration-700 ease-snap",
                    "agent:bg-brand",
                    "drop:bg-(--campaign-color)",
                    "renaissance:bg-brand",
                    full && "bg-subtle-foreground/60 agent:bg-subtle-foreground/60 drop:bg-subtle-foreground/60 renaissance:bg-subtle-foreground/60",
                  )}
                  style={{ transform: `scaleX(${Math.min(1, share)})` }}
                />
              </span>
            </dd>
          </div>

          <div className="flex items-center justify-between gap-3 renaissance:py-3">
            <dt className={label}>Payout</dt>
            <dd className="flex items-center gap-2 text-muted-foreground">
              <Lock className="size-3.5" aria-hidden />
              <span aria-hidden className="flex gap-1">
                <span className="h-3 w-5 rounded-full bg-foreground/15 blur-[2px]" />
                <span className="h-3 w-8 rounded-full bg-foreground/15 blur-[2px]" />
              </span>
              <span className="sr-only">Hidden until you sign up</span>
            </dd>
          </div>
        </dl>

        <Link
          href={publicCampaignSignupHref(campaign.id)}
          className={cn(
            "pressable group/cta inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 text-[15px] font-semibold",
            "outline-offset-2 transition-[background-color,color,box-shadow] duration-200 ease-snap",
            full
              ? "text-foreground ring-1 ring-border-strong ring-inset hover:bg-surface-2"
              : cn(
                  "bg-foreground text-background hover:bg-foreground/85",
                  "agent:bg-brand agent:text-brand-foreground agent:hover:bg-brand/90",
                  "drop:bg-(--campaign-color) drop:text-(--campaign-ink) drop:hover:brightness-110",
                ),
            "renaissance:rounded-[var(--radius-sm)]",
          )}
        >
          <span>
            Sign up to see payout<span className="sr-only">: {campaign.title}</span>
          </span>
          <ArrowRight
            className="size-4 transition-transform duration-200 ease-snap group-hover/cta:translate-x-0.5"
            aria-hidden
          />
        </Link>
      </div>
    </article>
  );
}

const chip = cn(
  "inline-flex h-7 items-center gap-1.5 rounded-full border bg-surface-2/70 px-2.5 text-xs font-medium whitespace-nowrap text-foreground/85",
  "[&_svg]:size-3.5 [&_svg]:shrink-0 [&_svg]:text-muted-foreground",
  "renaissance:rounded-[var(--radius-sm)] renaissance:bg-transparent",
  "agent:border-transparent agent:bg-surface-2",
);

const label = "text-xs font-medium text-muted-foreground renaissance:font-mono renaissance:text-[11px] renaissance:tracking-[0.06em] renaissance:uppercase";

export { PublicCampaignCard };
