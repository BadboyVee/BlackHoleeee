"use client";

import { useEffect, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarPlus, Check, Clock, Send, ShieldCheck, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { fieldDescribedBy } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import {
  CLAIM_RULES,
  REQUEST_NOTE_MAX,
  REQUEST_NOTE_MIN,
  requestNoteSchema,
  type RequestNoteValues,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { formatUtcTime } from "@/lib/time";
import { cn } from "@/lib/utils";

import { BrandTile } from "../brand-tile";
import { Burst } from "../burst";
import { useClaim, useClaimActions } from "../claim-store";
import { useCreatorDemo } from "../creator-data";
import { Money } from "../money";
import { springArrive, springPop, stagger } from "../motion";
import { CreatorSheet, SheetActions, useSheetSession } from "../sheet";
import { RollingNumber } from "../slots";
import { formatUtcWindow, LocalWhen, LocalWindow } from "../time";
import { displayType } from "../ui";
import { downloadCampaignCalendar } from "./calendar";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function CampaignLine({ campaign }: { campaign: CreatorCampaign }) {
  return (
    <div className="flex items-center gap-3">
      <BrandTile initials={campaign.brand.initials} color={campaign.brand.color} size="md" />
      <div className="min-w-0">
        <p className="truncate text-[15px] font-semibold tracking-[-0.015em]">{campaign.title}</p>
        <p className="truncate text-xs text-muted-foreground">{campaign.brand.name}</p>
      </div>
    </div>
  );
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2.5 text-sm">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="min-w-0 text-right">{children}</span>
    </div>
  );
}

function WindowFacts({ campaign }: { campaign: CreatorCampaign }) {
  return (
    <>
      <Fact label="Post window">
        <LocalWindow start={campaign.timing.postWindowStart} end={campaign.timing.postWindowEnd} className="block font-medium" />
        <span className="block text-xs text-muted-foreground">
          {formatUtcWindow(campaign.timing.postWindowStart, campaign.timing.postWindowEnd)}
        </span>
      </Fact>
      <Fact label="Proof due">
        <LocalWhen value={campaign.timing.proofDeadline} className="block font-medium" />
        <span className="block text-xs text-muted-foreground">{formatUtcTime(campaign.timing.proofDeadline)}</span>
      </Fact>
    </>
  );
}

/* --------------------------------------------------------------- instant */

type Phase = "confirm" | "working" | "done";

/**
 * Instant claim. First the facts and the rules, then the moment it lands:
 * the slots counter rolls down, a burst in the brand's colors, your angle,
 * your window and next steps, and a calendar file.
 */
export function ConfirmClaimSheet({
  campaign,
  slotsLeft,
  open,
  onOpenChange,
}: {
  campaign: CreatorCampaign;
  slotsLeft: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const session = useSheetSession(open);
  const [state, setState] = useState<{ session: number; phase: Phase }>({ session, phase: "confirm" });
  const phase = state.session === session ? state.phase : "confirm";
  const setPhase = (next: Phase) => setState({ session, phase: next });

  return (
    <CreatorSheet
      open={open}
      onOpenChange={(next) => {
        if (phase !== "working") onOpenChange(next);
      }}
      title={phase === "done" ? "You're in" : "Claim this slot?"}
      description={phase === "done" ? undefined : "It's yours the moment you confirm."}
      hideHeader={phase === "done"}
    >
      <ConfirmFlow
        key={session}
        campaign={campaign}
        slotsLeft={slotsLeft}
        phase={phase}
        setPhase={setPhase}
        onClose={() => onOpenChange(false)}
      />
    </CreatorSheet>
  );
}

function ConfirmFlow({
  campaign,
  slotsLeft,
  phase,
  setPhase,
  onClose,
}: {
  campaign: CreatorCampaign;
  slotsLeft: number;
  phase: Phase;
  setPhase: (phase: Phase) => void;
  onClose: () => void;
}) {
  const { me } = useCreatorDemo();
  const actions = useClaimActions();
  const claim = useClaim(campaign.id);
  const [before, setBefore] = useState<number | null>(null);
  const [rolled, setRolled] = useState(false);
  const [burst, setBurst] = useState(0);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  async function confirm() {
    setPhase("working");
    await wait(650);
    setBefore(slotsLeft);
    if (!actions.claim(campaign, me.id)) {
      toast.error("You already have this one");
      onClose();
      return;
    }
    setPhase("done");
    setBurst((value) => value + 1);
    timer.current = setTimeout(() => setRolled(true), 450);
  }

  if (phase !== "done") {
    return (
      <div className="flex flex-col gap-5">
        <CampaignLine campaign={campaign} />
        <div className="divide-y rounded-xl border px-4">
          <Fact label="You'll be paid">
            <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="md" />
          </Fact>
          <WindowFacts campaign={campaign} />
          {campaign.draftRequired ? <Fact label="Draft">Approved before you post</Fact> : null}
        </div>
        <div className="rounded-xl bg-surface-2/70 p-4">
          <p className="mb-2.5 flex items-center gap-2 text-sm font-semibold">
            <ShieldCheck className="size-4 text-muted-foreground" /> The rules
          </p>
          <ul className="flex flex-col gap-2">
            {CLAIM_RULES.map((rule) => (
              <li key={rule} className="flex items-start gap-2.5 text-sm text-pretty text-muted-foreground">
                <Check className="mt-0.5 size-4 shrink-0 text-(--tone-green)" strokeWidth={2.5} />
                {rule}
              </li>
            ))}
          </ul>
        </div>
        <SheetActions>
          <Button variant="ghost" size="xl" onClick={onClose} disabled={phase === "working"}>
            Not now
          </Button>
          <Button variant="brand" size="xl" loading={phase === "working"} onClick={confirm} className="sm:min-w-44">
            {phase === "working" ? "Claiming" : "Confirm claim"}
          </Button>
        </SheetActions>
      </div>
    );
  }

  const shownLeft = !rolled && before !== null ? before : slotsLeft;
  return (
    <div className="flex flex-col gap-5" role="status">
      <div className="relative -mx-5 flex flex-col items-center overflow-visible px-5 pt-2 pb-1 text-center sm:-mx-6 sm:px-6">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -top-10 bottom-0"
          style={{
            background: `radial-gradient(55% 75% at 50% 35%, color-mix(in oklab, ${campaign.brand.color} 24%, transparent), transparent 72%)`,
          }}
        />
        <div className="relative flex size-24 items-center justify-center">
          <Burst color={campaign.brand.color} burstKey={burst} />
          <motion.span
            initial={{ scale: 0.3, rotate: -24 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={springPop}
            className="relative flex size-[4.25rem] items-center justify-center rounded-full text-white shadow-float"
            style={{ backgroundColor: campaign.brand.color }}
          >
            <Check className="size-9" strokeWidth={3} />
          </motion.span>
        </div>
        <motion.h3
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springArrive, delay: 0.08 }}
          className={cn(displayType, "relative mt-3 text-[2.25rem] leading-none")}
        >
          You&apos;re in
        </motion.h3>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.16 }}
          className="relative mt-2.5 text-sm text-pretty text-muted-foreground"
        >
          Your slot on {campaign.title} is held.{" "}
          <span className="inline-flex items-baseline gap-1 font-semibold whitespace-nowrap text-foreground">
            <RollingNumber value={shownLeft} /> of {campaign.slots} left
          </span>{" "}
          for everyone else.
        </motion.p>
      </div>

      {claim?.angle ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springArrive, delay: 0.12 }}
          className="rounded-xl bg-foreground p-4 text-background"
        >
          <p className="flex items-center gap-1.5 text-label opacity-70">
            <Sparkles className="size-3.5" /> Your angle
          </p>
          <p className="mt-1.5 text-[15px] leading-snug font-semibold text-pretty">{claim.angle}</p>
        </motion.div>
      ) : null}

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...springArrive, delay: 0.18 }}
        className="divide-y rounded-xl border px-4"
      >
        <WindowFacts campaign={campaign} />
      </motion.div>

      <div>
        <p className="mb-2.5 text-sm font-semibold">Next steps</p>
        <ol className="flex flex-col gap-2">
          {[
            campaign.draftRequired ? "Write your draft and send it for a quick check." : "Read the brief and your angle.",
            campaign.draftRequired
              ? "Once it's approved, post it inside your window."
              : "Post inside your window, with the paid partnership label on.",
            "Paste your post link here before the proof deadline.",
          ].map((step, index) => (
            <motion.li
              key={step}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...springArrive, delay: 0.24 + stagger(index, 0.06) }}
              className="flex items-start gap-3 text-sm text-pretty"
            >
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-3 font-mono text-xs font-semibold">
                {index + 1}
              </span>
              <span className="pt-0.5">{step}</span>
            </motion.li>
          ))}
        </ol>
      </div>

      <SheetActions>
        <Button variant="secondary" size="xl" onClick={() => downloadCampaignCalendar(campaign, { angle: claim?.angle })}>
          <CalendarPlus />
          Add to calendar
        </Button>
        <Button size="xl" onClick={onClose} className="sm:min-w-32">
          Done
        </Button>
      </SheetActions>
    </div>
  );
}

/* ----------------------------------------------------------------- apply */

/** Apply mode: a short note to the agency. It doesn't hold a slot. */
export function RequestSheet({
  campaign,
  open,
  onOpenChange,
}: {
  campaign: CreatorCampaign;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const session = useSheetSession(open);
  const [sent, setSent] = useState<{ session: number; note: string } | null>(null);
  const note = sent?.session === session ? sent.note : null;

  return (
    <CreatorSheet
      open={open}
      onOpenChange={onOpenChange}
      title={note ? "Request sent" : "Request to join"}
      description={note ? undefined : "The agency picks the creators for this one."}
      hideHeader={Boolean(note)}
    >
      {note ? (
        <RequestSent note={note} onClose={() => onOpenChange(false)} />
      ) : (
        <RequestForm key={session} campaign={campaign} onSent={(value) => setSent({ session, note: value })} onClose={() => onOpenChange(false)} />
      )}
    </CreatorSheet>
  );
}

function RequestForm({
  campaign,
  onSent,
  onClose,
}: {
  campaign: CreatorCampaign;
  onSent: (note: string) => void;
  onClose: () => void;
}) {
  const actions = useClaimActions();
  const form = useForm<RequestNoteValues>({
    resolver: zodResolver(requestNoteSchema),
    defaultValues: { note: "" },
    mode: "onTouched",
  });
  const note = useWatch({ control: form.control, name: "note" }) ?? "";
  const length = note.trim().length;
  const error = form.formState.errors.note?.message;

  const submit = form.handleSubmit(async (values) => {
    await wait(600);
    if (!actions.request(campaign, values.note)) {
      toast.error("You already asked to join this one");
      onClose();
      return;
    }
    onSent(values.note);
  });

  return (
    <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
      <CampaignLine campaign={campaign} />
      <div className="grid gap-2">
        <label htmlFor="request-note" className="text-sm font-medium">
          Why you, in a line or two
        </label>
        <Textarea
          id="request-note"
          rows={4}
          placeholder="Your audience, a post that did well, or the angle you'd take"
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={fieldDescribedBy("request-note", { hint: true, error })}
          {...form.register("note")}
        />
        <div className="flex items-start justify-between gap-3 text-[13px]">
          {error ? (
            <p id="request-note-error" role="alert" className="text-destructive-text">
              {error}
            </p>
          ) : (
            <p id="request-note-hint" className="text-muted-foreground">
              {REQUEST_NOTE_MIN} to {REQUEST_NOTE_MAX} characters. The agency reads every one.
            </p>
          )}
          <span
            className={cn(
              "shrink-0 tabular",
              length > REQUEST_NOTE_MAX
                ? "text-destructive-text"
                : length >= REQUEST_NOTE_MIN
                  ? "text-(--tone-green)"
                  : "text-muted-foreground",
            )}
          >
            {length}/{REQUEST_NOTE_MAX}
          </span>
        </div>
      </div>
      <div className="divide-y rounded-xl border px-4">
        <Fact label="If accepted, you're paid">
          <Money amount={campaign.payout.amount} currency={campaign.payout.currency} size="md" />
        </Fact>
        <WindowFacts campaign={campaign} />
      </div>
      <p className="rounded-xl bg-surface-2/70 p-4 text-sm text-pretty text-muted-foreground">
        A request doesn&apos;t hold a slot. If the agency accepts it, the slot is yours and the usual rules apply: one claim
        per campaign, drop it before your window starts, proof by the deadline.
      </p>
      <SheetActions>
        <Button type="button" variant="ghost" size="xl" onClick={onClose} disabled={form.formState.isSubmitting}>
          Not now
        </Button>
        <Button type="submit" variant="brand" size="xl" loading={form.formState.isSubmitting} className="sm:min-w-44">
          {form.formState.isSubmitting ? "Sending" : "Send request"}
        </Button>
      </SheetActions>
    </form>
  );
}

function RequestSent({ note, onClose }: { note: string; onClose: () => void }) {
  return (
    <div className="flex flex-col gap-5" role="status">
      <div className="flex flex-col items-center pt-3 text-center">
        <motion.span
          initial={{ scale: 0.3, rotate: 30, x: -24, y: 12 }}
          animate={{ scale: 1, rotate: 0, x: 0, y: 0 }}
          transition={springPop}
          className="flex size-[4.25rem] items-center justify-center rounded-full bg-foreground text-background shadow-float"
        >
          <Send className="size-7" />
        </motion.span>
        <motion.h3
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springArrive, delay: 0.08 }}
          className={cn(displayType, "mt-4 text-[2.25rem] leading-none")}
        >
          Request sent
        </motion.h3>
        <p className="mt-2.5 max-w-sm text-sm text-pretty text-muted-foreground">
          It doesn&apos;t hold a slot. The agency reviews every request, and you&apos;ll get a notification and an email
          as soon as they decide.
        </p>
      </div>
      <figure className="rounded-xl border bg-surface-2/60 p-4">
        <figcaption className="mb-1.5 text-label text-subtle-foreground">Your note</figcaption>
        <blockquote className="text-sm text-pretty">{note}</blockquote>
      </figure>
      <p className="flex items-center justify-center gap-1.5 text-center text-xs text-pretty text-muted-foreground">
        <Clock className="size-3.5 shrink-0" /> Requests still waiting when claiming closes are declined.
      </p>
      <SheetActions>
        <Button size="xl" onClick={onClose} className="sm:min-w-32">
          Done
        </Button>
      </SheetActions>
    </div>
  );
}

/* ------------------------------------------------------------------ drop */

export function DropSheet({
  campaign,
  requested,
  open,
  onOpenChange,
  onConfirm,
}: {
  campaign: CreatorCampaign;
  requested: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}) {
  return (
    <CreatorSheet
      open={open}
      onOpenChange={onOpenChange}
      title={requested ? "Withdraw your request?" : "Drop this claim?"}
      description={requested ? "The agency won't see it any more." : "Your slot opens up for someone else straight away."}
    >
      <div className="flex flex-col gap-4">
        <CampaignLine campaign={campaign} />
        <p className="rounded-xl bg-surface-2/70 p-4 text-sm text-pretty text-muted-foreground">
          Each campaign can be claimed once, so you won&apos;t be able to claim it again yourself. If you change your mind
          later, message the agency.
        </p>
        <SheetActions>
          <Button variant="secondary" size="xl" onClick={() => onOpenChange(false)}>
            Keep it
          </Button>
          <Button variant="destructive" size="xl" onClick={onConfirm}>
            {requested ? "Withdraw request" : "Drop claim"}
          </Button>
        </SheetActions>
      </div>
    </CreatorSheet>
  );
}
