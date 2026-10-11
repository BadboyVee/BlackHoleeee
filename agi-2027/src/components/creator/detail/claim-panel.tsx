"use client";

import { useState } from "react";
import {
  CalendarPlus,
  CircleSlash,
  Clock3,
  FileText,
  FlaskConical,
  Link2,
  MessageSquareText,
  PartyPopper,
  Send,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { canDropClaim, claimClock, nextStep, type CreatorClaim } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { claimStatusMeta } from "@/lib/statuses";
import { formatTime, formatUtcTime } from "@/lib/time";
import { cn } from "@/lib/utils";

import { Burst } from "../burst";
import { useClaimActions } from "../claim-store";
import { shortReference } from "../claim-row";
import { useCreatorDemo } from "../creator-data";
import { useHydrated } from "../hooks";
import { Money } from "../money";
import { pressed, springArrive, springMove, springPop } from "../motion";
import { LocalWhen, TimeLeft } from "../time";
import { displayType, panel } from "../ui";
import { downloadCampaignCalendar } from "./calendar";
import { DraftEditor } from "./draft-editor";
import { ProofForm } from "./proof-form";

const CELEBRATE = new Set(["claimed", "draft_approved", "approved", "paid"]);

function Callout({ tone, icon: Icon, title, children }: { tone: "amber" | "red" | "green" | "blue"; icon: LucideIcon; title: string; children?: React.ReactNode }) {
  return (
    <div data-tone={tone} className="flex items-start gap-3 rounded-xl border border-(--tone-fg)/30 bg-(--tone-fg)/[0.07] p-3.5">
      <Icon className="mt-0.5 size-4 shrink-0 text-(--tone-fg)" />
      <div className="min-w-0 text-sm text-pretty">
        <p className="font-semibold text-(--tone-fg)">{title}</p>
        {children ? <div className="mt-0.5 text-foreground/85">{children}</div> : null}
      </div>
    </div>
  );
}

/** What you sent, while the agency has it. */
function Waiting({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-surface-2/50 p-4">
      <p className="flex items-center gap-2 text-label text-muted-foreground">
        <Icon className="size-3.5" />
        {title}
      </p>
      <div className="text-sm text-pretty text-muted-foreground">{children}</div>
    </div>
  );
}

function StepBody({ campaign, claim, now }: { campaign: CreatorCampaign; claim: CreatorClaim; now: number | null }) {
  switch (claim.status) {
    case "requested":
      return (
        <Waiting icon={Send} title="Your note">
          <p className="text-[15px] text-foreground/90">&ldquo;{claim.note ?? "No note"}&rdquo;</p>
        </Waiting>
      );
    case "claimed":
      return campaign.draftRequired ? <DraftEditor campaign={campaign} claim={claim} /> : <ProofForm campaign={campaign} claim={claim} now={now} />;
    case "changes_requested":
      return (
        <div className="flex flex-col gap-4">
          <Callout tone="amber" icon={MessageSquareText} title="The agency asked for changes">
            {claim.feedback ?? "Edit your draft and send it again."}
          </Callout>
          <DraftEditor campaign={campaign} claim={claim} />
        </div>
      );
    case "draft_submitted":
      return (
        <Waiting icon={FileText} title="Your draft">
          <p className="text-[15px] whitespace-pre-line text-foreground/90">{claim.draft?.text ?? ""}</p>
          {claim.draft?.media.length ? (
            <p className="mt-2 text-xs">Attached: {claim.draft.media.map((file) => file.name).join(", ")}</p>
          ) : null}
        </Waiting>
      );
    case "draft_approved":
      return <ProofForm campaign={campaign} claim={claim} now={now} />;
    case "rejected":
      return (
        <div className="flex flex-col gap-4">
          <Callout tone="red" icon={Link2} title="Your proof needs a fix">
            {claim.feedback ?? "Fix the post and send the link again before the deadline."}
          </Callout>
          <ProofForm campaign={campaign} claim={claim} now={now} />
        </div>
      );
    case "proof_submitted":
      return (
        <Waiting icon={Link2} title="Your post">
          {claim.proof ? (
            <a
              href={claim.proof.url}
              target="_blank"
              rel="noreferrer"
              className="block truncate font-mono text-[13px] text-foreground underline decoration-border-strong underline-offset-4"
            >
              {claim.proof.url.replace("https://", "")}
            </a>
          ) : null}
          <p className="mt-2">The agency checks the link, the label and the tags.</p>
        </Waiting>
      );
    case "approved":
      return (
        <div className="flex items-center justify-between gap-4 rounded-xl border bg-surface-2/50 p-4">
          <div>
            <p className="text-xs text-muted-foreground">Your earning</p>
            <Money amount={claim.payout.amount} currency={claim.payout.currency} size="lg" className="mt-1" />
          </div>
          <StatusBadge kind="earning" status="unpaid" />
        </div>
      );
    case "paid":
      return (
        <div className="flex flex-col gap-3 rounded-xl border bg-surface-2/50 p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Paid</p>
              <Money amount={claim.payout.amount} currency={claim.payout.currency} size="lg" className="mt-1" />
            </div>
            <StatusBadge kind="earning" status="paid" />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-[13px] text-muted-foreground">
            {claim.paidAt ? (
              <span>
                Sent <LocalWhen value={claim.paidAt} className="text-foreground" />
              </span>
            ) : null}
            {claim.paidReference ? (
              <span className="font-mono text-xs">ref {shortReference(claim.paidReference)}</span>
            ) : null}
          </div>
        </div>
      );
    case "expired":
    case "cancelled":
      return (
        <Callout tone="blue" icon={CircleSlash} title={claimStatusMeta[claim.status].label}>
          {claim.feedback ?? [...claim.events].reverse().find((event) => event.note)?.note ?? claimStatusMeta[claim.status].description}
        </Callout>
      );
  }
}

/** Preview only: plays the agency's part so the whole loop can be tried. */
function AgencySimulator({ campaign, claim }: { campaign: CreatorCampaign; claim: CreatorClaim }) {
  const { me } = useCreatorDemo();
  const actions = useClaimActions();
  const firstTag = campaign.requiredTags.hashtags[0] ?? campaign.requiredTags.mentions[0];
  const say = (title: string, description?: string) => toast(title, { description });

  const options: { label: string; variant?: "secondary" | "destructive" | "default"; run: () => void }[] =
    {
      requested: [
        {
          label: "Accept request",
          variant: "default" as const,
          run: () => actions.accept(campaign, me.id) && say("Request accepted", "The slot is yours."),
        },
        { label: "Decline", run: () => actions.decline(campaign) && say("Request declined") },
      ],
      draft_submitted: [
        {
          label: "Approve draft",
          variant: "default" as const,
          run: () => actions.approveDraft(campaign) && say("Draft approved", "Post it inside your window."),
        },
        {
          label: "Ask for changes",
          run: () =>
            actions.requestChanges(
              campaign,
              `Lead with the moment that surprised you${firstTag ? `, and make sure ${firstTag} is in there` : ""}.`,
            ) && say("Changes requested"),
        },
      ],
      proof_submitted: [
        {
          label: "Approve proof",
          variant: "default" as const,
          run: () => actions.approveProof(campaign) && say("Proof approved", "Your earning is now Unpaid."),
        },
        {
          label: "Reject proof",
          run: () =>
            actions.rejectProof(
              campaign,
              "The paid partnership label is missing. Turn it on, repost and send the new link before the deadline.",
            ) && say("Proof rejected"),
        },
      ],
      approved: [
        {
          label: "Mark as paid",
          variant: "default" as const,
          run: () => actions.markPaid(campaign) && say("Marked as paid", "The reference is in Earnings."),
        },
      ],
    }[claim.status as "requested" | "draft_submitted" | "proof_submitted" | "approved"] ?? [];

  if (options.length === 0) return null;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springArrive}
      className="rounded-2xl border-2 border-dashed border-border-strong p-4"
    >
      <p className="flex items-center gap-1.5 text-label text-muted-foreground">
        <FlaskConical className="size-3.5" /> Preview only
      </p>
      <p className="mt-1.5 text-sm font-semibold">Simulate agency review</p>
      <p className="mt-0.5 text-[13px] text-pretty text-muted-foreground">
        In the real portal the agency does this from their review queue. Here you can play their part.
      </p>
      <div className={cn("mt-3 grid gap-2 sm:flex sm:flex-wrap", options.length > 1 && "grid-cols-2")}>
        {options.map((option) => (
          <motion.div key={option.label} whileTap={pressed} className="min-w-0">
            <Button variant={option.variant ?? "secondary"} size="lg" onClick={option.run} className="w-full px-3 sm:w-auto sm:px-5">
              {option.label}
            </Button>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

/** "Your claim": where you stand, what's next, and the form for it. */
export function ClaimPanel({
  campaign,
  claim,
  now,
  onDrop,
}: {
  campaign: CreatorCampaign;
  claim: CreatorClaim;
  now: number | null;
  onDrop: () => void;
}) {
  const hydrated = useHydrated();
  const step = nextStep(claim.status, campaign);
  const clock = now === null ? null : claimClock(claim.status, campaign.timing, now);
  const droppable = now !== null && canDropClaim(claim.status, campaign.timing, now);
  const active = !["expired", "cancelled", "paid"].includes(claim.status);
  const postingAhead = ["claimed", "draft_submitted", "changes_requested", "draft_approved", "rejected"].includes(claim.status);

  // A little celebration whenever the claim moves forward in a good way.
  const [seen, setSeen] = useState({ status: claim.status, burst: 0 });
  if (seen.status !== claim.status) {
    setSeen({ status: claim.status, burst: CELEBRATE.has(claim.status) ? seen.burst + 1 : seen.burst });
  }

  return (
    <motion.section
      id="your-claim"
      aria-labelledby="your-claim-title"
      layout="position"
      initial={hydrated ? { opacity: 0, y: 16 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={springArrive}
      className={cn(panel, "scroll-mt-24 overflow-hidden")}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-40"
        style={{
          background: `linear-gradient(to bottom, color-mix(in oklab, ${campaign.brand.color} 13%, transparent), transparent)`,
        }}
      />
      <div className="relative flex flex-col gap-5 p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-label text-subtle-foreground">Your claim</p>
            <AnimatePresence mode="popLayout" initial={false}>
              <motion.h2
                key={step.title}
                id="your-claim-title"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={springMove}
                className={cn(displayType, "mt-1.5 text-[1.625rem] leading-none sm:text-[1.875rem]")}
              >
                {step.title}
              </motion.h2>
            </AnimatePresence>
          </div>
          <div className="relative flex shrink-0 items-center">
            <Burst color={campaign.brand.color} burstKey={seen.burst} />
            <motion.span key={claim.status} initial={{ scale: 0.7 }} animate={{ scale: 1 }} transition={springPop}>
              <StatusBadge kind="claim" status={claim.status} className="h-7 px-2.5 text-[13px]" />
            </motion.span>
          </div>
        </div>

        <div className="-mt-2 flex flex-col gap-3">
          <p className="max-w-prose text-[15px] text-pretty text-muted-foreground">{step.detail}</p>
          <div className="flex flex-wrap gap-2">
            {clock ? (
              <span className="inline-flex h-8 items-center gap-1.5 rounded-full border bg-surface px-3 text-[13px]">
                <Clock3 className="size-3.5 text-muted-foreground" />
                <TimeLeft to={clock.to} prefix={clock.label} className="font-medium" />
              </span>
            ) : null}
            {claim.angle ? (
              <a
                href="#angles"
                className="inline-flex h-8 max-w-full items-center gap-1.5 rounded-full bg-foreground px-3 text-[13px] font-medium text-background"
              >
                <Sparkles className="size-3.5 shrink-0" />
                <span className="truncate">{claim.angle}</span>
              </a>
            ) : null}
            {claim.postTime ? (
              <span className="inline-flex h-8 items-center gap-1.5 rounded-full border bg-surface px-3 text-[13px]">
                Your post time {hydrated ? formatTime(claim.postTime) : formatTime(claim.postTime, "UTC")}
                <span className="text-muted-foreground">({formatUtcTime(claim.postTime)})</span>
              </span>
            ) : null}
          </div>
        </div>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={claim.status}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10, transition: { duration: 0.14 } }}
            transition={springArrive}
          >
            <StepBody campaign={campaign} claim={claim} now={now} />
          </motion.div>
        </AnimatePresence>

        <AgencySimulator campaign={campaign} claim={claim} />

        {active || droppable ? (
          <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-4">
            {postingAhead ? (
              <Button variant="ghost" size="lg" className="-ml-3" onClick={() => downloadCampaignCalendar(campaign, { angle: claim.angle })}>
                <CalendarPlus />
                Add to calendar
              </Button>
            ) : (
              <span />
            )}
            {droppable ? (
              <Button variant="ghost" size="lg" className="-mr-3 text-destructive-text hover:text-destructive-text" onClick={onDrop}>
                {claim.status === "requested" ? "Withdraw request" : "Drop this claim"}
              </Button>
            ) : null}
          </div>
        ) : null}

        {claim.status === "paid" ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <PartyPopper className="size-4" /> Nice work. On to the next one.
          </p>
        ) : null}
      </div>
    </motion.section>
  );
}
