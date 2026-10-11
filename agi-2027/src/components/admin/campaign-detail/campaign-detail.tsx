"use client";

import Link from "next/link";
import {
  CircleCheckBig,
  Copy,
  Ellipsis,
  FileText,
  Film,
  ImageIcon,
  Link2,
  Lock,
  Pause,
  Pencil,
  Play,
  Share2,
  SquareX,
  Users,
} from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { EmptyState } from "@/components/ui/empty-state";
import {
  audienceMeta,
  claimModeMeta,
  deliverableMeta,
  NEEDS_TARGET_POST,
  platformLabel,
} from "@/lib/campaigns/options";
import { campaignById, clientById, creatorById } from "@/lib/campaigns/demo";
import { formatMoney } from "@/lib/money";
import { campaignCommitment } from "@/lib/campaigns/schema";
import { cn } from "@/lib/utils";
import { AdminPageHeader } from "../admin-page-header";
import { BrandTile } from "../brand-tile";
import { audienceReach } from "../campaign-builder/steps/payout";
import { BriefPreview, CreatorCardPreview, previewFromCampaign, shortLink } from "../campaign-preview";
import { CampaignTimeline } from "../campaign-timeline";
import { statusActionCopy, statusActions } from "../campaigns/campaign-actions";
import { campaignStats, rosterFor } from "../demo-insights";
import { formatBytes } from "../file-drop-zone";
import { Panel } from "../panel";
import { previewOnly } from "../preview-toast";
import { LocalWhen, LocalWindow, utcText, utcWindowText } from "../time-text";
import { Roster } from "./roster";

const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const fileIcon = { image: ImageIcon, video: Film, document: FileText } as const;

function MoreMenu({ id, title, status }: { id: string; title: string; status: Parameters<typeof statusActions>[0] }) {
  const actions = statusActions(status);
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" size="icon" aria-label={`More actions for ${title}`}>
          <Ellipsis />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        {actions.pause ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.pause)}>
            <Pause />
            Pause
          </DropdownMenuItem>
        ) : null}
        {actions.resume ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.resume)}>
            <Play />
            Resume
          </DropdownMenuItem>
        ) : null}
        {actions.close ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.close)}>
            <SquareX />
            Close
          </DropdownMenuItem>
        ) : null}
        {actions.complete ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.complete)}>
            <CircleCheckBig />
            Mark complete
          </DropdownMenuItem>
        ) : null}
        {actions.pause || actions.resume || actions.close || actions.complete ? <DropdownMenuSeparator /> : null}
        <DropdownMenuItem
          onSelect={() => previewOnly("Copies a private report link for the client, with every approved post and the totals. Client reports arrive in Milestone 10.")}
        >
          <Share2 />
          Copy client report link
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href={`/admin/campaigns/new?from=${id}`}>
            <Copy />
            Duplicate
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function Stat({ label, value, detail, children }: { label: string; value: React.ReactNode; detail?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="flex min-h-[6.5rem] flex-col justify-between bg-surface p-4 sm:p-5">
      <p className="text-[13px] text-muted-foreground">{label}</p>
      <p className="mt-2.5 text-figure text-[1.75rem] leading-none">{value}</p>
      {children}
      {detail ? <p className="mt-2 truncate text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-0.5 px-4 py-2.5 sm:grid-cols-[9rem_minmax(0,1fr)] sm:gap-4 sm:px-5">
      <dt className="text-[13px] text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-[13px] break-words">{children}</dd>
    </div>
  );
}

/** One campaign from the owner's side: who's on it, what they see, and the setup. */
export function CampaignDetail({ campaignId }: { campaignId: string }) {
  const campaign = campaignById(campaignId);
  if (!campaign) return null;
  const client = clientById(campaign.clientId);
  const stats = campaignStats(campaign);
  const roster = rosterFor(campaign);
  const model = previewFromCampaign(campaign, client);
  const commitment = campaignCommitment(campaign);
  const reach = audienceReach(campaign.audience);
  const t = campaign.timing;
  const filled = campaign.slots ? campaign.slotsTaken / campaign.slots : 0;
  const unpaid = roster.filter((row) => row.status === "approved").length;
  const { audience } = campaign;
  const audienceDetail =
    audience.kind === "tiers"
      ? audience.tiers.join(", ")
      : audience.kind === "tags"
        ? audience.tags.join(", ")
        : audience.kind === "creators"
          ? audience.creatorIds.map((id) => creatorById(id)?.name ?? id).join(", ")
          : "";

  const statusLine =
    campaign.status === "draft" ? (
      <>Draft. Creators can&apos;t see it yet.</>
    ) : campaign.status === "scheduled" && t.dropAt ? (
      <>
        Drops <LocalWhen value={t.dropAt} />
        <span className="text-subtle-foreground"> ({utcText(t.dropAt)})</span>
      </>
    ) : campaign.droppedAt ? (
      <>
        Dropped <LocalWhen value={campaign.droppedAt} />
      </>
    ) : null;

  return (
    <>
      <AdminPageHeader
        leading={<BrandTile initials={client?.initials ?? "?"} color={client?.color} size="xl" className="mt-0.5 hidden sm:inline-flex" />}
        eyebrow={
          <span className="inline-flex flex-wrap items-center gap-x-1.5">
            <span className="font-medium text-foreground">{client?.name}</span>
            <span aria-hidden>·</span>
            {deliverableMeta[campaign.deliverable].label} on {platformLabel[campaign.platform]}
          </span>
        }
        title={campaign.title}
        description={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[14px]">
            <StatusBadge kind="campaign" status={campaign.status} />
            {statusLine ? <span>{statusLine}</span> : null}
          </span>
        }
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href={`/admin/campaigns/${campaign.id}/edit`}>
                <Pencil aria-hidden />
                Edit
              </Link>
            </Button>
            <Button asChild variant="ghost" className="hidden sm:inline-flex">
              <Link href={`/admin/campaigns/new?from=${campaign.id}`}>
                <Copy aria-hidden />
                Duplicate
              </Link>
            </Button>
            <MoreMenu id={campaign.id} title={campaign.title} status={campaign.status} />
          </>
        }
      />

      <div className="grid grid-cols-2 overflow-hidden rounded-lg border bg-border shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)] [gap:1px] sm:grid-cols-3 xl:grid-cols-6">
        <Stat label="Slots taken" value={`${campaign.slotsTaken}/${campaign.slots}`}>
          <div className="mt-2.5 h-1 overflow-hidden rounded-full bg-surface-3">
            <div className={cn("h-full rounded-full", filled >= 1 ? "bg-subtle-foreground" : "bg-foreground/70")} style={{ width: `${Math.round(filled * 100)}%` }} />
          </div>
        </Stat>
        <Stat
          label="Requests waiting"
          value={stats.requests}
          detail={campaign.claimMode === "apply" ? "Apply mode: you accept each" : "Instant claim, no requests"}
        />
        <Stat label="Posts live" value={stats.postsLive} detail={`${stats.waiting} waiting for review`} />
        <Stat label="Approved" value={stats.approved} detail={unpaid ? `${unpaid} not paid yet` : "All paid"} />
        <Stat label="Paid" value={stats.paid} detail={commitment ? `Up to ${formatMoney(commitment.high, commitment.currency)}` : undefined} />
        <Stat label="Total views" value={stats.views ? compact.format(stats.views) : "0"} detail="From creators' metrics" />
      </div>

      <Panel
        id="roster"
        className="mt-4"
        title="Roster"
        description="Everyone on the campaign. Set angles and post times here; pick rows for bulk actions."
        action={
          <span className="inline-flex items-center gap-1.5 text-[13px] text-muted-foreground tabular">
            <Users className="size-3.5" aria-hidden />
            {roster.length}
          </span>
        }
      >
        {roster.length ? (
          <Roster campaign={campaign} initialRows={roster} />
        ) : (
          <EmptyState
            className="m-4 border-dashed"
            icon={Users}
            title="Nobody on it yet"
            description={
              campaign.status === "scheduled" && t.dropAt ? (
                <>
                  It drops <LocalWhen value={t.dropAt} />. Claims show up here live, and you can hand out angles and post
                  times as they come in.
                </>
              ) : (
                "Publish it or schedule the drop, and claims show up here live."
              )
            }
            action={
              <Button asChild variant="secondary">
                <Link href={`/admin/campaigns/${campaign.id}/edit`}>
                  <Pencil aria-hidden />
                  {campaign.status === "draft" ? "Finish and publish" : "Edit the campaign"}
                </Link>
              </Button>
            }
          />
        )}
      </Panel>

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
        <Panel id="creator-view" title="What creators see" description="The card on their board, then the brief." bodyClassName="grid gap-3 p-4">
          <CreatorCardPreview model={model} />
          <BriefPreview model={model} />
        </Panel>

        <div className="grid content-start gap-4">
          <Panel id="timing" title="Timing" description="In your time, with UTC beside it." bodyClassName="grid gap-4 px-4 pt-4 pb-2 sm:px-5">
            <CampaignTimeline
              drop={campaign.droppedAt ?? (campaign.status === "scheduled" ? t.dropAt : "")}
              claimDeadline={t.claimDeadline}
              postWindowStart={t.postWindowStart}
              postWindowEnd={t.postWindowEnd}
              proofDeadline={t.proofDeadline}
            />
            <dl className="-mx-4 divide-y border-t sm:-mx-5">
              <Row label="Post window">
                <LocalWindow start={t.postWindowStart} end={t.postWindowEnd} />
                <span className="block text-xs text-subtle-foreground">{utcWindowText(t.postWindowStart, t.postWindowEnd)}</span>
              </Row>
              <Row label="Claiming closes">
                <LocalWhen value={t.claimDeadline} />
                <span className="block text-xs text-subtle-foreground">{utcText(t.claimDeadline)}</span>
              </Row>
              <Row label="Proof is due">
                <LocalWhen value={t.proofDeadline} />
                <span className="block text-xs text-subtle-foreground">{utcText(t.proofDeadline)}</span>
              </Row>
            </dl>
          </Panel>

          <Panel id="setup" title="Setup">
            <dl className="divide-y">
              <Row label="Audience">
                {audienceMeta[audience.kind].label}
                {audienceDetail ? `: ${audienceDetail}` : ""}
                <span className="block text-xs text-subtle-foreground">
                  {reach.length} {reach.length === 1 ? "creator" : "creators"} can see it
                </span>
              </Row>
              <Row label="Claim mode">{claimModeMeta[campaign.claimMode].label}</Row>
              <Row label="Payout">
                {formatMoney(campaign.payout.amount, campaign.payout.currency)} per post
                {campaign.tierPayouts.map((row) => (
                  <span key={row.tier} className="block text-xs text-muted-foreground">
                    {row.tier}: {formatMoney(row.amount, campaign.payout.currency)}
                  </span>
                ))}
                {campaign.creatorPayouts.map((row) => (
                  <span key={row.creatorId} className="block text-xs text-muted-foreground">
                    {creatorById(row.creatorId)?.name}: {formatMoney(row.amount, campaign.payout.currency)}
                  </span>
                ))}
              </Row>
              <Row label="Rules">
                {campaign.paidLabelRequired ? "Paid partnership label required" : "No paid label"}
                <span className="block text-xs text-muted-foreground">
                  {campaign.draftRequired ? "Drafts approved before posting" : "No draft step"}
                </span>
              </Row>
              {NEEDS_TARGET_POST.has(campaign.deliverable) && campaign.links.targetPostUrl ? (
                <Row label={campaign.deliverable === "quote" ? "Post to quote" : "Post to reply to"}>
                  <a href={campaign.links.targetPostUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline decoration-border-strong underline-offset-4">
                    <Link2 className="size-3.5" aria-hidden />
                    {shortLink(campaign.links.targetPostUrl)}
                  </a>
                </Row>
              ) : null}
              <Row label="Assets">
                {campaign.assets.files.length || campaign.assets.brandKitUrl ? (
                  <ul className="grid gap-1">
                    {campaign.assets.files.map((file) => {
                      const Icon = fileIcon[file.kind];
                      return (
                        <li key={file.name} className="flex items-center gap-1.5">
                          <Icon className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
                          <span className="truncate">{file.name}</span>
                          <span className="shrink-0 text-xs text-subtle-foreground">{formatBytes(file.sizeBytes)}</span>
                        </li>
                      );
                    })}
                    {campaign.assets.brandKitUrl ? (
                      <li className="flex items-center gap-1.5">
                        <Link2 className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
                        Brand kit: {shortLink(campaign.assets.brandKitUrl)}
                      </li>
                    ) : null}
                  </ul>
                ) : (
                  <span className="text-subtle-foreground">None</span>
                )}
              </Row>
            </dl>
          </Panel>

          <Panel
            id="internal"
            title="Internal"
            action={
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <Lock className="size-3" aria-hidden />
                Team only
              </span>
            }
          >
            <dl className="divide-y">
              <Row label="Notes">{campaign.internal.notes || <span className="text-subtle-foreground">None</span>}</Row>
              <Row label="Budget">
                {campaign.internal.budgetAmount ? (
                  <>
                    {formatMoney(campaign.internal.budgetAmount, campaign.internal.budgetCurrency)}
                    {commitment && campaign.internal.budgetCurrency === commitment.currency ? (
                      <span
                        className={cn(
                          "block text-xs",
                          Number(commitment.high) > Number(campaign.internal.budgetAmount) ? "text-destructive-text" : "text-muted-foreground",
                        )}
                      >
                        Every slot paid costs up to {formatMoney(commitment.high, commitment.currency)}
                      </span>
                    ) : null}
                  </>
                ) : (
                  <span className="text-subtle-foreground">Not set</span>
                )}
              </Row>
            </dl>
          </Panel>
        </div>
      </div>
    </>
  );
}
