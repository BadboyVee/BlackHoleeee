"use client";

import {
  BadgeCheck,
  Check,
  Download,
  ExternalLink,
  FileText,
  Film,
  Image as ImageGlyph,
  Link2,
  Sparkles,
  X,
} from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { XLogo } from "@/components/brand/social-icons";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { deliverableMeta, platformLabel } from "@/lib/campaigns/options";
import { cn } from "@/lib/utils";

import { CopyButton } from "../copy-button";
import { pressed, springArrive, stagger } from "../motion";
import { Reveal } from "../reveal";
import { displayType, panel } from "../ui";

/** A titled block on the campaign page. */
export function DetailSection({
  id,
  title,
  kicker,
  action,
  children,
  className,
}: {
  id: string;
  title: string;
  kicker?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Reveal inView>
      <section aria-labelledby={`${id}-title`} id={id} className={cn(panel, "scroll-mt-24 p-5 sm:p-6", className)}>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {kicker ? <p className="mb-1.5 text-label text-subtle-foreground">{kicker}</p> : null}
            <h2 id={`${id}-title`} className={cn(displayType, "text-xl leading-none sm:text-[1.375rem]")}>
              {title}
            </h2>
          </div>
          {action}
        </div>
        {children}
      </section>
    </Reveal>
  );
}

export function BriefSection({ campaign }: { campaign: CreatorCampaign }) {
  const { brief } = campaign;
  return (
    <DetailSection id="brief" kicker="The brief" title="What to post">
      <div className="flex flex-col gap-5 text-[15px] leading-relaxed">
        <div>
          <h3 className="mb-1 text-sm font-semibold">About {campaign.brand.name}</h3>
          <p className="text-pretty text-muted-foreground">{brief.about}</p>
        </div>
        <div>
          <h3 className="mb-1 text-sm font-semibold">What to say</h3>
          <p className="text-pretty text-muted-foreground">{brief.whatToSay}</p>
        </div>
        <figure
          className="relative overflow-hidden rounded-xl border bg-surface-2/60 p-4 sm:p-5"
          style={{ borderLeftColor: campaign.brand.color, borderLeftWidth: 4 }}
        >
          <figcaption className="mb-1.5 text-label text-subtle-foreground">Key message</figcaption>
          <blockquote className="text-lg leading-snug font-semibold tracking-[-0.02em] text-balance">
            &ldquo;{brief.keyMessage}&rdquo;
          </blockquote>
        </figure>
        <div className="grid gap-3 sm:grid-cols-2">
          <ListCard tone="green" title="Do" items={brief.dos} icon="check" />
          <ListCard tone="red" title="Don't" items={brief.donts} icon="x" />
        </div>
      </div>
    </DetailSection>
  );
}

function ListCard({ tone, title, items, icon }: { tone: "green" | "red"; title: string; items: string[]; icon: "check" | "x" }) {
  const Icon = icon === "check" ? Check : X;
  return (
    <div data-tone={tone} className="rounded-xl border p-4">
      <p className="mb-2.5 text-sm font-semibold">{title}</p>
      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2.5 text-sm text-pretty">
            <span className="mt-0.5 flex size-[18px] shrink-0 items-center justify-center rounded-full bg-(--tone-fg)/12 text-(--tone-fg)">
              <Icon className="size-3" strokeWidth={3} />
            </span>
            <span className="text-foreground/90">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AnglesSection({
  campaign,
  angle,
  pending,
}: {
  campaign: CreatorCampaign;
  /** The angle assigned to this creator, once claimed. */
  angle?: string;
  /** Claimed but not assigned yet (a request waiting for the agency). */
  pending: boolean;
}) {
  if (campaign.angles.length === 0) return null;
  return (
    <DetailSection
      id="angles"
      kicker="Angles"
      title={angle ? "Your angle" : "Pick up an angle"}
      action={
        angle ? null : (
          <span className="mt-1 text-right text-xs text-pretty text-muted-foreground">
            {pending ? "Assigned when you're accepted" : "Assigned when you claim"}
          </span>
        )
      }
    >
      <ul className="flex flex-col gap-2">
        {campaign.angles.map((item, index) => {
          const mine = item === angle;
          return (
            <motion.li
              key={item}
              layout="position"
              initial={false}
              animate={{ opacity: angle && !mine ? 0.55 : 1 }}
              transition={springArrive}
              className={cn(
                "relative flex items-center gap-3 rounded-xl border px-4 py-3 text-[15px]",
                mine ? "border-foreground bg-foreground text-background shadow-float" : "bg-surface-2/40",
              )}
            >
              <span
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full font-mono text-xs font-semibold",
                  mine ? "bg-background/15" : "bg-surface-3 text-muted-foreground",
                )}
              >
                {mine ? <Sparkles className="size-3.5" /> : index + 1}
              </span>
              <span className="min-w-0 flex-1 text-pretty">{item}</span>
              {mine ? (
                <span className="shrink-0 rounded-full bg-background/15 px-2 py-0.5 text-[11px] font-semibold tracking-wide uppercase">
                  Yours
                </span>
              ) : null}
            </motion.li>
          );
        })}
      </ul>
    </DetailSection>
  );
}

export function DeliverableSection({ campaign }: { campaign: CreatorCampaign }) {
  const deliverable = deliverableMeta[campaign.deliverable];
  return (
    <DetailSection id="deliverable" kicker="Deliverable" title={deliverable.label}>
      <div className="flex items-start gap-3.5">
        <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-foreground text-background">
          {campaign.platform === "x" ? <XLogo className="size-[18px]" /> : <Film className="size-5" />}
        </span>
        <div className="min-w-0 text-[15px]">
          <p className="font-semibold">
            {deliverable.label} on {platformLabel[campaign.platform]}
          </p>
          <p className="mt-0.5 text-sm text-pretty text-muted-foreground">{deliverable.hint}</p>
          {campaign.draftRequired ? (
            <p className="mt-2 text-sm text-pretty">
              <span className="font-semibold">Draft first.</span>{" "}
              <span className="text-muted-foreground">The agency approves your draft before you post.</span>
            </p>
          ) : null}
        </div>
      </div>
    </DetailSection>
  );
}

function LinkRow({ label, url }: { label: string; url: string }) {
  const display = url.replace(/^https?:\/\//, "");
  return (
    <li className="flex items-center gap-3 rounded-xl border bg-surface-2/40 py-2 pr-2 pl-4">
      <div className="min-w-0 flex-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="truncate font-mono text-[13px]">{display}</p>
      </div>
      <a
        href={url}
        target="_blank"
        rel="noreferrer"
        aria-label={`Open ${label.toLowerCase()}`}
        className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
      >
        <ExternalLink className="size-4" />
      </a>
      <CopyButton value={url} label={`Copy ${label.toLowerCase()}`} iconOnly toastMessage="Link copied" />
    </li>
  );
}

export function LinksSection({ campaign }: { campaign: CreatorCampaign }) {
  const { targetPostUrl, trackingUrl } = campaign.links;
  if (!targetPostUrl && !trackingUrl) return null;
  return (
    <DetailSection id="links" kicker="Links" title="Links to use">
      <ul className="flex flex-col gap-2">
        {targetPostUrl ? (
          <LinkRow label={campaign.deliverable === "reply" ? "Post to reply to" : "Post to quote"} url={targetPostUrl} />
        ) : null}
        {trackingUrl ? <LinkRow label="Tracking link to include" url={trackingUrl} /> : null}
      </ul>
    </DetailSection>
  );
}

export function TagsSection({ campaign }: { campaign: CreatorCampaign }) {
  const { mentions, hashtags, keywords } = campaign.requiredTags;
  const all = [...mentions, ...hashtags, ...keywords];
  if (all.length === 0) return null;
  const groups = [
    { label: "Mention", items: mentions },
    { label: "Hashtag", items: hashtags },
    { label: "Keyword", items: keywords },
  ].filter((group) => group.items.length);
  return (
    <DetailSection
      id="tags"
      kicker="Required"
      title="Tags to include"
      action={<CopyButton value={all.join(" ")} label="Copy all" copiedLabel="Copied" toastMessage="Tags copied" />}
    >
      <div className="flex flex-col gap-3">
        {groups.map((group) => (
          <div key={group.label} className="flex flex-wrap items-center gap-2">
            <span className="w-[4.5rem] shrink-0 text-xs text-muted-foreground">{group.label}</span>
            {group.items.map((tag) => (
              <span
                key={tag}
                className="inline-flex h-8 items-center rounded-full border bg-surface-2/60 px-3 font-mono text-[13px] font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        ))}
      </div>
    </DetailSection>
  );
}

function sizeLabel(bytes: number) {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1000))} KB`;
}

export function AssetsSection({ campaign }: { campaign: CreatorCampaign }) {
  const { files, brandKitUrl } = campaign.assets;
  if (files.length === 0 && !brandKitUrl) return null;
  return (
    <DetailSection id="assets" kicker="Assets" title="Files to use">
      <ul className="flex flex-col gap-2">
        {files.map((file, index) => {
          const Icon = file.kind === "image" ? ImageGlyph : file.kind === "video" ? Film : FileText;
          return (
            <motion.li
              key={file.name}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ ...springArrive, delay: stagger(index) }}
              className="flex items-center gap-3 rounded-xl border bg-surface-2/40 py-2 pr-2 pl-3"
            >
              <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-surface-3 text-muted-foreground">
                <Icon className="size-[18px]" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {file.kind === "document" ? "File" : file.kind === "image" ? "Image" : "Video"} · {sizeLabel(file.sizeBytes)}
                </p>
              </div>
              <motion.button
                type="button"
                whileTap={pressed}
                onClick={() =>
                  toast("Downloads arrive with real campaigns", {
                    description: `${file.name} is sample data in this preview.`,
                  })
                }
                className="inline-flex h-11 shrink-0 cursor-pointer items-center gap-1.5 rounded-full border border-border-strong bg-surface px-3.5 text-[13px] font-medium hover:bg-surface-2"
              >
                <Download className="size-4" />
                Download
              </motion.button>
            </motion.li>
          );
        })}
        {brandKitUrl ? (
          <li className="flex items-center gap-3 rounded-xl border border-dashed py-2 pr-2 pl-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-surface-3 text-muted-foreground">
              <Link2 className="size-[18px]" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">Brand kit</p>
              <p className="truncate font-mono text-xs text-muted-foreground">{brandKitUrl.replace(/^https?:\/\//, "")}</p>
            </div>
            <a
              href={brandKitUrl}
              target="_blank"
              rel="noreferrer"
              className="pressable inline-flex h-11 shrink-0 items-center gap-1.5 rounded-full border border-border-strong bg-surface px-3.5 text-[13px] font-medium hover:bg-surface-2"
            >
              Open
              <ExternalLink className="size-3.5" />
            </a>
          </li>
        ) : null}
      </ul>
    </DetailSection>
  );
}

export function PaidLabelNote({ campaign }: { campaign: CreatorCampaign }) {
  if (!campaign.paidLabelRequired) return null;
  return (
    <Reveal inView>
      <aside
        data-tone="blue"
        className="flex items-start gap-3.5 rounded-2xl border border-(--tone-fg)/25 bg-surface p-4 shadow-soft sm:p-5"
      >
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-(--tone-fg)/12 text-(--tone-fg)">
          <BadgeCheck className="size-5" />
        </span>
        <div className="text-sm text-pretty">
          <p className="font-semibold">Turn on the paid partnership label</p>
          <p className="mt-0.5 text-muted-foreground">
            It&apos;s required on every paid post. On X, switch on &ldquo;Paid partnership&rdquo; before you post.
            Proof without it gets sent back.
          </p>
        </div>
      </aside>
    </Reveal>
  );
}
