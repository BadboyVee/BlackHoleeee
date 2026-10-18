"use client";

import { Suspense, useMemo } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ChevronRight,
  CircleAlert,
  Clock,
  FileText,
  Link2,
  PenLine,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";

import { AccountFirstName } from "@/components/auth/account-context";
import { CampaignCard } from "@/components/campaign/campaign-card";
import { toCardData } from "@/components/campaign/card-data";
import { Skeleton } from "@/components/ui/skeleton";
import {
  attentionFor,
  BOARD_STATUSES,
  claimClock,
  earningsFromClaims,
  earningsSummary,
  type AttentionKind,
  type CreatorClaim,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { formatDateTime } from "@/lib/time";
import { cn } from "@/lib/utils";

import { Carousel, CarouselItem } from "./carousel";
import { useClaims } from "./claim-store";
import { ClaimRow } from "./claim-row";
import { useCreatorDemo } from "./creator-data";
import { useHydrated, useMediaQuery, useNow } from "./hooks";
import { Money } from "./money";
import { pressed, springArrive, stagger } from "./motion";
import { Reveal } from "./reveal";
import { TimeLeft } from "./time";
import { panel, SectionHeading } from "./ui";

const SETTLED = new Set(["approved", "paid", "expired", "cancelled"]);

const attentionCopy: Record<AttentionKind, { title: string; tone: "amber" | "red" | "blue"; icon: LucideIcon; cta: string }> = {
  changes_requested: { title: "Changes requested", tone: "amber", icon: PenLine, cta: "Edit draft" },
  rejected: { title: "Proof needs a fix", tone: "red", icon: CircleAlert, cta: "Fix it" },
  proof_due: { title: "Proof due", tone: "red", icon: Link2, cta: "Add link" },
  draft_due: { title: "Draft due soon", tone: "amber", icon: FileText, cta: "Write it" },
  window_soon: { title: "Your window opens soon", tone: "blue", icon: Clock, cta: "Get ready" },
};

type Pair = { campaign: CreatorCampaign; claim: CreatorClaim };

function useHomeData() {
  const { campaigns, claims: seed } = useCreatorDemo();
  const claims = useClaims();
  const now = useNow(60_000);

  return useMemo(() => {
    const byId = new Map(campaigns.map((campaign) => [campaign.id, campaign]));
    const claimFor = new Map(claims.map((claim) => [claim.campaignId, claim]));
    const seedFor = new Map(seed.map((claim) => [claim.campaignId, claim.status]));

    const drops = campaigns
      .filter((campaign) => BOARD_STATUSES.includes(campaign.status) && !claimFor.has(campaign.id))
      .filter((campaign) => now === null || new Date(campaign.timing.claimDeadline).getTime() > now)
      .sort((a, b) => new Date(b.droppedAt).getTime() - new Date(a.droppedAt).getTime())
      .map((campaign) => toCardData(campaign, { seedStatus: seedFor.get(campaign.id), now }));

    const mine: Pair[] = claims.flatMap((claim) => {
      const campaign = byId.get(claim.campaignId);
      return campaign ? [{ campaign, claim }] : [];
    });
    const active = mine
      .filter(({ claim }) => !SETTLED.has(claim.status))
      .sort((a, b) => {
        const at = (pair: Pair) => (now === null ? null : claimClock(pair.claim.status, pair.campaign.timing, now)?.to);
        const ta = at(a);
        const tb = at(b);
        return (ta ? new Date(ta).getTime() : Infinity) - (tb ? new Date(tb).getTime() : Infinity);
      });
    const attention =
      now === null
        ? []
        : active.flatMap((pair) => {
            const kind = attentionFor(pair.claim.status, pair.campaign.timing, now, pair.campaign);
            return kind ? [{ ...pair, kind }] : [];
          });
    const earnings = earningsSummary(earningsFromClaims(mine.map((pair) => pair.claim)));
    const open = drops.filter((drop) => drop.status === "live").length;

    return { drops, active, attention, earnings, open, now };
  }, [campaigns, claims, seed, now]);
}

function summaryLine(open: number, needs: number) {
  const drops =
    open === 0 ? "No open drops right now" : `${open} ${open === 1 ? "campaign is" : "campaigns are"} open to claim`;
  const you = needs === 0 ? "nothing needs you yet" : `${needs} ${needs === 1 ? "thing needs" : "things need"} you`;
  return `${drops}, and ${you}.`;
}

function Hero({ open, needs }: { open: number; needs: number }) {
  const { me } = useCreatorDemo();
  const hydrated = useHydrated();
  const now = useNow(60_000);
  const today = now === null ? null : formatDateTime(new Date(now)).split(",")[0];

  return (
    <section aria-labelledby="hello" className="pt-2 pb-1 sm:pt-4">
      <p className="mb-3 h-5 text-label text-muted-foreground">
        {today ? (
          <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {today}
          </motion.span>
        ) : null}
      </p>
      <h1 id="hello" className="text-h1 text-balance">
        Hey{" "}
        <Suspense fallback={<span className="invisible">{me.firstName}</span>}>
          <AccountFirstName fallback={me.firstName} />
        </Suspense>
      </h1>
      <div className="mt-3 min-h-[1.6em] max-w-xl text-[1.0625rem] leading-relaxed text-pretty text-muted-foreground sm:text-lg">
        {hydrated ? (
          <motion.p initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={springArrive}>
            {summaryLine(open, needs)}
          </motion.p>
        ) : (
          <Skeleton className="h-5 w-72 max-w-full" />
        )}
      </div>
    </section>
  );
}

function AttentionList({ items, now }: { items: (Pair & { kind: AttentionKind })[]; now: number }) {
  return (
    <section aria-labelledby="attention">
      <SectionHeading id="attention" title="Needs you" count={items.length} />
      <ul className="flex flex-col gap-2.5">
        {items.map(({ campaign, claim, kind }, index) => {
          const copy = attentionCopy[kind];
          const Icon = copy.icon;
          const clock = claimClock(claim.status, campaign.timing, now);
          return (
            <motion.li
              key={campaign.id}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springArrive, delay: stagger(index) }}
              whileTap={pressed}
              className="list-none"
            >
              <Link
                href={`/dashboard/campaigns/${campaign.id}#your-claim`}
                data-tone={copy.tone}
                className="group relative flex items-start gap-3.5 overflow-hidden rounded-2xl border border-(--tone-fg)/30 bg-surface p-4 shadow-soft transition-[border-color,box-shadow] duration-300 hover:border-(--tone-fg)/50 hover:shadow-float"
              >
                <span aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_100%_at_0%_0%,color-mix(in_oklab,var(--tone-fg)_11%,transparent),transparent_70%)]" />
                <span className="relative flex size-11 shrink-0 items-center justify-center rounded-xl bg-(--tone-fg)/12 text-(--tone-fg)">
                  <Icon className="size-5" />
                </span>
                <span className="relative min-w-0 flex-1">
                  <span className="block text-xs font-semibold tracking-[0.02em] text-(--tone-fg) uppercase">{copy.title}</span>
                  <span className="mt-1 block truncate text-[15px] font-semibold tracking-[-0.015em]">{campaign.title}</span>
                  {claim.feedback && (kind === "changes_requested" || kind === "rejected") ? (
                    <span className="mt-1 line-clamp-2 block text-sm text-pretty text-muted-foreground">
                      &ldquo;{claim.feedback}&rdquo;
                    </span>
                  ) : null}
                  <span className="mt-2.5 flex items-center justify-between gap-3 text-[13px]">
                    {clock ? (
                      <TimeLeft to={clock.to} prefix={clock.label} className="font-mono text-xs font-medium" />
                    ) : (
                      <span />
                    )}
                    <span className="inline-flex items-center gap-0.5 font-semibold">
                      {copy.cta}
                      <ChevronRight className="size-4 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
                    </span>
                  </span>
                </span>
              </Link>
            </motion.li>
          );
        })}
      </ul>
    </section>
  );
}

function EarningsCard({ earnings }: { earnings: ReturnType<typeof earningsSummary> }) {
  const groups = [
    { label: "Unpaid", rows: earnings.unpaid, hint: "Approved, on the way" },
    { label: "Paid", rows: earnings.paid, hint: "Sent, with a reference" },
  ];
  return (
    <section aria-labelledby="earnings">
      <SectionHeading id="earnings" title="Earnings" />
      <div className={cn(panel, "overflow-hidden")}>
        <div className="grid grid-cols-2 divide-x">
          {groups.map((group) => (
            <div key={group.label} className="flex flex-col gap-2 p-4 sm:p-5">
              <p className="text-xs font-medium text-muted-foreground">{group.label}</p>
              {group.rows.length ? (
                group.rows.map((row) => (
                  <Money key={row.currency} amount={row.amount} currency={row.currency} size="md" />
                ))
              ) : (
                <p className="text-figure text-[1.375rem] leading-none text-subtle-foreground">0</p>
              )}
              <p className="mt-auto pt-1 text-xs text-subtle-foreground">{group.hint}</p>
            </div>
          ))}
        </div>
        <Link
          href="/dashboard/earnings"
          className="group flex items-center justify-between gap-3 border-t bg-surface-2/40 px-4 py-3 text-[13px] transition-colors hover:bg-surface-2 sm:px-5"
        >
          <span className="text-muted-foreground">Totals stay per currency. USD and NGN never mix.</span>
          <ArrowRight className="size-4 shrink-0 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
        </Link>
      </div>
    </section>
  );
}

function DropsSkeleton() {
  return (
    <div className="-mx-4 flex gap-3 overflow-hidden px-4 pt-2 pb-5 sm:-mx-6 sm:px-6 lg:-mx-10 lg:px-10">
      {[0, 1, 2].map((key) => (
        <div key={key} className={cn(panel, "flex h-[21rem] w-[86%] max-w-[22rem] shrink-0 flex-col gap-4 p-5 sm:w-[21.5rem] xl:w-[calc((100%-1.5rem)/3)]")}>
          <div className="flex items-center gap-3">
            <Skeleton className="size-11 rounded-xl" />
            <div className="flex flex-1 flex-col gap-2">
              <Skeleton className="h-3.5 w-28" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-5 w-4/5" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="mt-auto h-8 w-32" />
        </div>
      ))}
    </div>
  );
}

function ListSkeleton({ rows = 2 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: rows }, (_, key) => (
        <div key={key} className={cn(panel, "flex flex-col gap-3.5 p-4 sm:p-5")}>
          <div className="flex items-center gap-3">
            <Skeleton className="size-11 rounded-xl" />
            <div className="flex flex-1 flex-col gap-2">
              <Skeleton className="h-4 w-48 max-w-full" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <Skeleton className="h-1.5 w-full" />
          <Skeleton className="h-3.5 w-40" />
        </div>
      ))}
    </div>
  );
}

function EmptyNote({ icon: Icon, title, children, action }: { icon: LucideIcon; title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className={cn(panel, "flex flex-col items-center px-6 py-10 text-center shadow-none")}>
      <span className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground">
        <Icon className="size-5" />
      </span>
      <p className="text-[15px] font-semibold tracking-[-0.015em]">{title}</p>
      <p className="mt-1 max-w-xs text-sm text-pretty text-muted-foreground">{children}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

/** The creator's home: new drops, what you're on, what needs you, and what you've earned. */
function CreatorHome() {
  const hydrated = useHydrated();
  const desktop = useMediaQuery("(min-width: 1024px)");
  const { drops, active, attention, earnings, open, now } = useHomeData();
  const needsYou =
    hydrated && now !== null && attention.length > 0 ? (
      <motion.div
        key="attention"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.98 }}
        transition={springArrive}
      >
        <AttentionList items={attention} now={now} />
      </motion.div>
    ) : null;

  return (
    <div className="flex flex-col gap-10 sm:gap-12">
      <Hero open={open} needs={attention.length} />

      <AnimatePresence initial={false}>{desktop ? null : needsYou}</AnimatePresence>

      <section aria-labelledby="new-drops" className="min-w-0">
        <SectionHeading
          id="new-drops"
          title="New drops"
          count={hydrated ? drops.length : undefined}
          action={
            <Link
              href="/dashboard/campaigns"
              className="group inline-flex h-11 items-center gap-1 rounded-full pl-3 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              See all
              <ArrowRight className="size-4 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
            </Link>
          }
        />
        {!hydrated ? (
          <DropsSkeleton />
        ) : drops.length ? (
          <Carousel label="New drops">
            {drops.map((drop, index) => (
              <CarouselItem key={drop.href}>
                <CampaignCard campaign={drop} index={index} />
              </CarouselItem>
            ))}
          </Carousel>
        ) : (
          <EmptyNote icon={Sparkles} title="You're all caught up">
            New campaigns land here the moment they drop. We&apos;ll let you know.
          </EmptyNote>
        )}
      </section>

      <div className="grid gap-10 sm:gap-12 lg:grid-cols-[minmax(0,1fr)_21rem] lg:gap-8">
        <section aria-labelledby="active" className="min-w-0">
          <SectionHeading
            id="active"
            title="Your active campaigns"
            count={hydrated ? active.length : undefined}
            action={
              <Link
                href="/dashboard/my-campaigns"
                className="group inline-flex h-11 items-center gap-1 rounded-full pl-3 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                See all
                <ArrowRight className="size-4 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
              </Link>
            }
          />
          {!hydrated ? (
            <ListSkeleton />
          ) : active.length ? (
            <ul className="flex flex-col gap-3">
              {active.map(({ campaign, claim }, index) => (
                <ClaimRow key={campaign.id} campaign={campaign} claim={claim} now={now} index={index} />
              ))}
            </ul>
          ) : (
            <EmptyNote
              icon={Sparkles}
              title="Nothing on the go"
              action={
                <Link
                  href="/dashboard/campaigns"
                  className="pressable inline-flex h-11 items-center gap-2 rounded-full bg-foreground px-5 text-sm font-semibold text-background"
                >
                  Browse campaigns
                </Link>
              }
            >
              Claim a campaign and it shows up here with a countdown to your window.
            </EmptyNote>
          )}
        </section>

        <div className="flex min-w-0 flex-col gap-10 sm:gap-12 lg:gap-8">
          <AnimatePresence initial={false}>{desktop ? needsYou : null}</AnimatePresence>
          {hydrated ? (
            <Reveal>
              <EarningsCard earnings={earnings} />
            </Reveal>
          ) : (
            <div>
              <SectionHeading title="Earnings" />
              <Skeleton className="h-44 w-full rounded-2xl" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export { CreatorHome };
