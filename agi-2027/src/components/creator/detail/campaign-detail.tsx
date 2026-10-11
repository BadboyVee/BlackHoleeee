"use client";

import { useState } from "react";
import { ArrowDown, BadgeCheck, CalendarPlus, Check, Lock, PenLine, Send, Zap } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { XLogo } from "@/components/brand/social-icons";
import { effectiveSlots } from "@/components/campaign/card-data";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  claimAvailability,
  claimClock,
  CLAIM_RULES,
  isNewDrop,
  nextStep,
  type ClaimAvailability,
  type CreatorClaim,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { deliverableMeta, platformLabel } from "@/lib/campaigns/options";
import type { CampaignStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";

import { BrandTile, brandWash } from "../brand-tile";
import { useClaim, useClaimActions, useSeedClaim } from "../claim-store";
import { useCampaignLookup } from "../creator-data";
import { useHydrated, useNow } from "../hooks";
import { Money } from "../money";
import { pressed, springArrive, springMove } from "../motion";
import { RollingNumber, SlotsMeter } from "../slots";
import { TimeLeft } from "../time";
import { Chip, NewBadge } from "../ui";
import {
  AnglesSection,
  AssetsSection,
  BriefSection,
  DeliverableSection,
  LinksSection,
  PaidLabelNote,
  TagsSection,
} from "./brief";
import { downloadCampaignCalendar } from "./calendar";
import { ClaimPanel } from "./claim-panel";
import { ConfirmClaimSheet, DropSheet, RequestSheet } from "./claim-sheets";
import { StatusTimeline, TimingSection } from "./timelines";

type Slots = { taken: number; left: number; status: CampaignStatus };

/** One or two words for why claiming is blocked, for buttons and tiles. */
const blockedLabel: Partial<Record<ClaimAvailability["state"], string>> = {
  full: "Full",
  closed: "Closed",
  deadline_passed: "Closed",
  paused: "Paused",
  not_open: "Not open yet",
  not_in_audience: "Not for you",
};

function Stat({ label, children, className }: { label: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-2 rounded-xl border bg-surface/80 p-3.5 backdrop-blur-sm sm:p-4", className)}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {children}
    </div>
  );
}

/** The clock that matters on this page: the claim's own countdown, else the claim deadline. */
function ClockStat({
  campaign,
  claim,
  availability,
  now,
}: {
  campaign: CreatorCampaign;
  claim?: CreatorClaim;
  availability: ClaimAvailability | null;
  now: number | null;
}) {
  if (now === null || !availability) {
    return (
      <Stat label="Claim closes in">
        <Skeleton className="h-7 w-24" />
      </Stat>
    );
  }
  const clock = claim ? claimClock(claim.status, campaign.timing, now) : null;
  if (clock) {
    return (
      <Stat label={clock.label.replace(/ in$/, "")}>
        <TimeLeft to={clock.to} className="text-figure text-[1.625rem] leading-none" />
      </Stat>
    );
  }
  if (!claim && availability.canClaim) {
    return (
      <Stat label="Claim closes in">
        <TimeLeft to={campaign.timing.claimDeadline} endedLabel="Closed" className="text-figure text-[1.625rem] leading-none" />
      </Stat>
    );
  }
  return (
    <Stat label={claim ? "Status" : "Claiming"}>
      <p className="text-figure text-[1.625rem] leading-none">
        {claim ? nextStep(claim.status, campaign).title : (blockedLabel[availability.state] ?? availability.title)}
      </p>
    </Stat>
  );
}

function DetailHeader({
  campaign,
  claim,
  slots,
  availability,
  ready,
  now,
}: {
  campaign: CreatorCampaign;
  claim?: CreatorClaim;
  slots: Slots;
  availability: ClaimAvailability | null;
  ready: boolean;
  now: number | null;
}) {
  const deliverable = deliverableMeta[campaign.deliverable].label;
  const host = campaign.brand.website.replace(/^https?:\/\//, "");
  const fresh = ready && now !== null && !claim && Boolean(availability?.canClaim) && isNewDrop(campaign.droppedAt, now);

  return (
    <header className="relative overflow-hidden rounded-2xl border bg-surface shadow-soft">
      <div aria-hidden className="pointer-events-none absolute inset-0" style={brandWash(campaign.brand.color, 22)} />
      <div className="relative flex flex-col gap-5 p-5 sm:p-7">
        <div className="flex items-center gap-3.5">
          <BrandTile initials={campaign.brand.initials} color={campaign.brand.color} size="lg" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-[15px] font-semibold tracking-[-0.015em]">{campaign.brand.name}</p>
            <p className="truncate text-sm text-muted-foreground">
              {campaign.brand.xHandle}
              {host ? ` · ${host}` : ""}
            </p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1.5 sm:flex-row sm:items-center">
            {fresh ? <NewBadge /> : null}
            <StatusBadge kind="campaign" status={slots.status} />
          </div>
        </div>

        <div>
          <h1 className="text-h2 text-balance">{campaign.title}</h1>
          <p className="mt-3 max-w-2xl text-[1.0625rem] leading-relaxed text-pretty text-muted-foreground">{campaign.summary}</p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          <Chip>
            {campaign.platform === "x" ? <XLogo className="size-3 text-foreground" /> : null}
            {deliverable} on {platformLabel[campaign.platform]}
          </Chip>
          <Chip>
            {campaign.claimMode === "instant" ? <Zap /> : <Send />}
            {campaign.claimMode === "instant" ? "Instant claim" : "Apply to join"}
          </Chip>
          {campaign.draftRequired ? (
            <Chip>
              <PenLine />
              Draft first
            </Chip>
          ) : null}
          {campaign.paidLabelRequired ? (
            <Chip>
              <BadgeCheck />
              Paid label
            </Chip>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
          <Stat label="You earn" className="col-span-2 sm:col-span-1">
            <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="xl" />
            <p className="text-xs text-muted-foreground">per post, paid in {campaign.payout.currency}</p>
          </Stat>
          <Stat label="Slots left">
            {ready ? (
              <p className="flex items-baseline gap-1.5">
                <RollingNumber value={slots.left} className="text-figure text-[1.625rem] leading-none" />
                <span className="text-sm text-muted-foreground">of {campaign.slots}</span>
              </p>
            ) : (
              <Skeleton className="h-7 w-16" />
            )}
            <SlotsMeter total={campaign.slots} taken={ready ? slots.taken : campaign.slotsTaken} className="mt-0.5" />
          </Stat>
          <ClockStat campaign={campaign} claim={claim} availability={availability} now={now} />
        </div>
      </div>
    </header>
  );
}

/** The main button for this campaign, whatever state it's in. */
function ClaimButton({
  availability,
  claim,
  campaign,
  onClaim,
  onRequest,
  className,
}: {
  availability: ClaimAvailability | null;
  claim?: CreatorClaim;
  campaign: CreatorCampaign;
  onClaim: () => void;
  onRequest: () => void;
  className?: string;
}) {
  if (!availability) return <Skeleton className={cn("h-12 w-36 rounded-full", className)} />;
  if (claim) {
    const step = nextStep(claim.status, campaign);
    return (
      <Button asChild size="xl" className={className}>
        <a href="#your-claim">
          {step.actor === "you" ? "Next step" : "Your claim"}
          <ArrowDown />
        </a>
      </Button>
    );
  }
  if (availability.state === "instant") {
    return (
      <motion.div whileTap={pressed} className={className}>
        <Button variant="brand" size="xl" onClick={onClaim} className="w-full shadow-[0_10px_24px_-10px_var(--brand)]">
          <Zap />
          Claim
        </Button>
      </motion.div>
    );
  }
  if (availability.state === "apply") {
    return (
      <motion.div whileTap={pressed} className={className}>
        <Button variant="brand" size="xl" onClick={onRequest} className="w-full shadow-[0_10px_24px_-10px_var(--brand)]">
          <Send />
          Request to join
        </Button>
      </motion.div>
    );
  }
  return (
    <Button size="xl" disabled className={className}>
      <Lock />
      {blockedLabel[availability.state] ?? availability.title}
    </Button>
  );
}

/** Phones: a floating bar with the payout and the main action. */
function ClaimBar(props: {
  campaign: CreatorCampaign;
  claim?: CreatorClaim;
  slots: Slots;
  availability: ClaimAvailability | null;
  onClaim: () => void;
  onRequest: () => void;
}) {
  const { campaign, claim, slots, availability } = props;
  return (
    <motion.div
      initial={{ y: "140%" }}
      animate={{ y: 0 }}
      transition={{ ...springArrive, delay: 0.1 }}
      className="fixed inset-x-0 bottom-0 z-40 px-3 pb-[max(env(safe-area-inset-bottom),0.625rem)] lg:hidden"
    >
      <div className="mx-auto flex max-w-md items-center gap-3 rounded-[1.75rem] border border-border-strong/70 bg-surface/90 p-2 pl-4 shadow-float backdrop-blur-xl backdrop-saturate-150">
        <div className="min-w-0 flex-1">
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.div
              key={claim ? `claim-${claim.status}` : availability?.state ?? "loading"}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={springMove}
            >
              {claim ? (
                <>
                  <StatusBadge kind="claim" status={claim.status} />
                  <p className="mt-1 truncate text-[13px] font-medium">{nextStep(claim.status, campaign).title}</p>
                </>
              ) : availability && !availability.canClaim ? (
                <p className="line-clamp-2 text-[13px] leading-snug text-pretty text-muted-foreground">{availability.detail}</p>
              ) : (
                <>
                  <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="md" />
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {availability ? `${slots.left} of ${campaign.slots} left` : " "}
                  </p>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
        <ClaimButton {...props} className="shrink-0" />
      </div>
    </motion.div>
  );
}

/** Desktop: the same action as a sticky card beside the brief. */
function SideCard(props: {
  campaign: CreatorCampaign;
  claim?: CreatorClaim;
  slots: Slots;
  availability: ClaimAvailability | null;
  onClaim: () => void;
  onRequest: () => void;
}) {
  const { campaign, claim, availability } = props;
  const step = claim ? nextStep(claim.status, campaign) : null;
  return (
    <div className="relative overflow-hidden rounded-2xl border bg-surface p-5 shadow-float">
      <div aria-hidden className="pointer-events-none absolute inset-0" style={brandWash(campaign.brand.color, 12)} />
      <div className="relative flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-muted-foreground">You earn</p>
            <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="lg" className="mt-1" />
          </div>
          {claim ? <StatusBadge kind="claim" status={claim.status} /> : null}
        </div>
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.div
            key={claim ? `claim-${claim.status}` : availability?.state ?? "loading"}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={springMove}
            className="text-sm text-pretty"
          >
            {step ? (
              <>
                <p className="font-semibold">{step.title}</p>
                <p className="mt-0.5 text-muted-foreground">{step.detail}</p>
              </>
            ) : availability ? (
              <>
                <p className="font-semibold">{availability.title}</p>
                <p className="mt-0.5 text-muted-foreground">{availability.detail}</p>
              </>
            ) : (
              <Skeleton className="h-10 w-full" />
            )}
          </motion.div>
        </AnimatePresence>
        <ClaimButton {...props} className="w-full" />
        {claim && !["expired", "cancelled", "requested"].includes(claim.status) ? (
          <Button variant="ghost" size="lg" onClick={() => downloadCampaignCalendar(campaign, { angle: claim.angle })}>
            <CalendarPlus />
            Add to calendar
          </Button>
        ) : null}
        {!claim && availability?.canClaim ? (
          <ul className="flex flex-col gap-1.5 border-t pt-4">
            {CLAIM_RULES.map((rule) => (
              <li key={rule} className="flex items-start gap-2 text-[13px] text-pretty text-muted-foreground">
                <Check className="mt-0.5 size-3.5 shrink-0 text-(--tone-green)" strokeWidth={2.5} />
                {rule}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

/** A campaign's own page: the brief, the claim flow and everything after it. */
function CampaignDetail({ campaignId }: { campaignId: string }) {
  const campaign = useCampaignLookup()(campaignId);
  const stored = useClaim(campaignId);
  const seed = useSeedClaim(campaignId);
  const actions = useClaimActions();
  const hydrated = useHydrated();
  const now = useNow(15_000);
  const [sheet, setSheet] = useState<"claim" | "request" | "drop" | null>(null);

  if (!campaign) return null;

  const ready = hydrated && now !== null;
  const claim = ready ? stored : undefined;
  const slots = effectiveSlots(campaign, seed?.status, ready ? stored : seed);
  const availability = ready
    ? claimAvailability({
        campaign: { ...campaign, status: slots.status, slotsTaken: slots.taken },
        now,
        inAudience: true,
        claim,
      })
    : null;
  const ctaProps = {
    campaign,
    claim,
    slots,
    availability,
    onClaim: () => setSheet("claim"),
    onRequest: () => setSheet("request"),
  };

  return (
    <article className="flex flex-col gap-6 pt-1 sm:pt-3">
      <DetailHeader campaign={campaign} claim={claim} slots={slots} availability={availability} ready={ready} now={now} />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20.5rem] lg:gap-8">
        <div className="flex min-w-0 flex-col gap-5">
          <AnimatePresence initial={false}>
            {claim ? (
              <motion.div
                key="claim"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={springMove}
              >
                <ClaimPanel campaign={campaign} claim={claim} now={now} onDrop={() => setSheet("drop")} />
              </motion.div>
            ) : null}
          </AnimatePresence>
          <BriefSection campaign={campaign} />
          <AnglesSection campaign={campaign} angle={claim?.angle} pending={claim?.status === "requested"} />
          <DeliverableSection campaign={campaign} />
          <LinksSection campaign={campaign} />
          <TagsSection campaign={campaign} />
          <AssetsSection campaign={campaign} />
          <TimingSection campaign={campaign} now={now} />
          <PaidLabelNote campaign={campaign} />
          <StatusTimeline campaign={campaign} claim={claim} />
        </div>
        <aside aria-label="Claim" className="hidden lg:block">
          <div className="sticky top-24">
            <SideCard {...ctaProps} />
          </div>
        </aside>
      </div>

      <ClaimBar {...ctaProps} />

      <ConfirmClaimSheet
        campaign={campaign}
        slotsLeft={slots.left}
        open={sheet === "claim"}
        onOpenChange={(open) => setSheet(open ? "claim" : null)}
      />
      <RequestSheet campaign={campaign} open={sheet === "request"} onOpenChange={(open) => setSheet(open ? "request" : null)} />
      <DropSheet
        campaign={campaign}
        requested={claim?.status === "requested"}
        open={sheet === "drop"}
        onOpenChange={(open) => setSheet(open ? "drop" : null)}
        onConfirm={() => {
          const wasRequest = claim?.status === "requested";
          if (actions.drop(campaign)) {
            toast(wasRequest ? "Request withdrawn" : "Claim dropped", {
              description: wasRequest ? undefined : "Your slot is open for someone else now.",
            });
          }
          setSheet(null);
        }}
      />
    </article>
  );
}

export { CampaignDetail };
