"use client";

import Link from "next/link";
import { motion } from "motion/react";
import {
  ArrowLeft,
  Bell,
  CalendarClock,
  Check,
  ClipboardCheck,
  FileText,
  Pencil,
  Plus,
  Rocket,
  Shuffle,
  Users,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { audienceMeta } from "@/lib/campaigns/options";
import type { DemoCampaign } from "@/lib/campaigns/demo";
import type { CampaignFormValues } from "@/lib/campaigns/schema";
import { adminTitleClass } from "../admin-page-header";
import { Callout } from "../form-field";
import { springArrive } from "../motion";
import { LocalWhen, utcText } from "../time-text";
import type { BuilderMode } from "./form-values";
import { audienceReach } from "./steps/payout";

type Step = { icon: React.ReactNode; title: React.ReactNode; body: React.ReactNode };

function whatHappensNext(values: CampaignFormValues, alreadyDropped: boolean): Step[] {
  const reach = audienceReach(values.audience).length;
  const audience = `${reach} ${reach === 1 ? "creator" : "creators"} (${audienceMeta[values.audience.kind].label.toLowerCase()})`;
  const notify: Step = {
    icon: <Bell className="size-4" />,
    title: "Creators are told three ways",
    body: (
      <>
        Everyone in the audience gets an in-app notification and an email, and the Telegram bot posts the drop in the
        creators group with a link to claim. Telegram arrives in Milestone 8.
      </>
    ),
  };
  const claim: Step =
    values.claimMode === "instant"
      ? {
          icon: <Users className="size-4" />,
          title: `The first ${values.slots} to tap Claim get a slot`,
          body: "Slots are counted inside the database the moment someone claims, so the campaign can never be overfilled. It shows as Full when the last slot goes.",
        }
      : {
          icon: <Users className="size-4" />,
          title: "Requests land in your review queue",
          body: `Creators send a short note. You accept up to ${values.slots}. A request doesn't hold a slot until you accept it.`,
        };
  const roster: Step = {
    icon: <Shuffle className="size-4" />,
    title: "Hand out angles and post times",
    body: "Open the campaign and give each creator an angle and a post time inside the window, from the roster.",
  };
  const proof: Step = {
    icon: <ClipboardCheck className="size-4" />,
    title: values.draftRequired ? "Drafts, then proof, come to you" : "Proof comes to you",
    body: values.draftRequired
      ? "Each creator sends a draft first. You approve it or ask for changes. After posting they paste the link, the free checks run, and you approve it."
      : "After posting, each creator pastes the link. The free checks run on X links, and you approve it in one tap.",
  };
  const pay: Step = {
    icon: <Wallet className="size-4" />,
    title: "Approved posts become earnings",
    body: "Each approval creates an Unpaid earning. Mark it paid with a reference from Payouts (Milestone 7).",
  };

  if (alreadyDropped) {
    return [
      {
        icon: <Pencil className="size-4" />,
        title: "The campaign updates in place",
        body: "Creators already on it get a note that the brief changed, in the app and by email. What they're paid doesn't change: each claim keeps the payout from when it was made.",
      },
      roster,
      proof,
    ];
  }
  const first: Step =
    values.publish === "now"
      ? {
          icon: <Rocket className="size-4" />,
          title: "It goes live straight away",
          body: `It appears on the campaign board for ${audience}, with the post window in each creator's own time and in UTC.`,
        }
      : values.publish === "schedule"
        ? {
            icon: <CalendarClock className="size-4" />,
            title: (
              <>
                It drops <LocalWhen value={values.timing.dropAt} />
              </>
            ),
            body: (
              <>
                That&apos;s {utcText(values.timing.dropAt)}. Until then it shows as Scheduled and only your team can see it.
                At that minute it goes live on its own for {audience}.
              </>
            ),
          }
        : {
            icon: <FileText className="size-4" />,
            title: "It stays a draft",
            body: "Only your team can see it. Open it from Campaigns when you're ready to publish it or schedule the drop. Nothing goes to creators until then.",
          };
  return values.publish === "draft" ? [first, notify, claim, pay] : [first, notify, claim, roster, proof, pay];
}

export function BuilderSuccess({
  values,
  mode,
  source,
  alreadyDropped,
  onKeepEditing,
  onCreateAnother,
}: {
  values: CampaignFormValues;
  mode: BuilderMode;
  source?: DemoCampaign;
  alreadyDropped: boolean;
  onKeepEditing: () => void;
  onCreateAnother: () => void;
}) {
  const heading = alreadyDropped
    ? "Your changes are ready"
    : values.publish === "now"
      ? "Ready to go live"
      : values.publish === "schedule"
        ? "Ready to drop on schedule"
        : "Ready as a draft";
  const steps = whatHappensNext(values, alreadyDropped);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springArrive}
      className="mx-auto grid max-w-2xl gap-6 py-4"
    >
      <div className="flex flex-col items-center text-center">
        <motion.span
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ ...springArrive, delay: 0.06 }}
          className="flex size-14 items-center justify-center rounded-full bg-foreground text-background shadow-float"
        >
          <Check className="size-7" strokeWidth={2.5} aria-hidden />
        </motion.span>
        <p className="mt-5 text-sm text-muted-foreground">{values.title}</p>
        <h2 className={adminTitleClass}>{heading}</h2>
        <p className="mt-2 max-w-md text-[15px] text-pretty text-muted-foreground">
          Every field checks out. Here&apos;s exactly what happens once saving is switched on.
        </p>
      </div>

      <Callout tone="warning" title="This preview doesn't save yet">
        Nothing was stored and nobody was notified. Saving and drops arrive in Milestone 5, notifications in Milestone 8.
        Your answers are still here if you keep editing.
      </Callout>

      <section aria-labelledby="next-title" className="overflow-hidden rounded-lg border bg-surface">
        <h3 id="next-title" className="border-b px-5 py-3 text-[14px] font-semibold">
          What happens next
        </h3>
        <ol className="grid gap-0 px-5 py-2">
          {steps.map((step, index) => (
            <motion.li
              key={index}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springArrive, delay: 0.1 + index * 0.04 }}
              className="relative flex gap-3.5 py-3"
            >
              <span className="relative flex flex-col items-center">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full border bg-surface-2 text-muted-foreground">
                  {step.icon}
                </span>
                {index < steps.length - 1 ? <span aria-hidden className="absolute top-9 -bottom-3 w-px bg-border" /> : null}
              </span>
              <div className="min-w-0 pt-1">
                <p className="text-sm font-medium">{step.title}</p>
                <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">{step.body}</p>
              </div>
            </motion.li>
          ))}
        </ol>
      </section>

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-center">
        <Button asChild variant="ghost">
          <Link href="/admin/campaigns">
            <ArrowLeft aria-hidden />
            Back to campaigns
          </Link>
        </Button>
        <Button variant="secondary" onClick={onKeepEditing}>
          <Pencil aria-hidden />
          Keep editing
        </Button>
        {mode === "edit" && source ? (
          <Button asChild>
            <Link href={`/admin/campaigns/${source.id}`}>Open the campaign</Link>
          </Button>
        ) : (
          <Button onClick={onCreateAnother}>
            <Plus aria-hidden />
            Create another
          </Button>
        )}
      </div>
    </motion.div>
  );
}
