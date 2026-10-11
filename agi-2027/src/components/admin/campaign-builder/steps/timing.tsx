"use client";

import { Controller, useWatch } from "react-hook-form";
import { CalendarClock, Clock, FileText, Rocket, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { publishMeta } from "@/lib/campaigns/options";
import { campaignStatusMeta } from "@/lib/statuses";
import { CampaignTimeline } from "../../campaign-timeline";
import { ChoiceCards } from "../../choice-cards";
import { DateTimeField } from "../../datetime-field";
import { Callout, FieldSection } from "../../form-field";
import { useNowMinute, useTimeZoneName } from "../../time-text";
import { suggestedTiming } from "../form-values";
import { useBuilder, useBuilderForm } from "../use-builder";

const publishIcon = {
  draft: <FileText className="size-4" />,
  now: <Rocket className="size-4" />,
  schedule: <CalendarClock className="size-4" />,
};

export function TimingStep() {
  const { control, setValue } = useBuilderForm();
  const { alreadyDropped, source } = useBuilder();
  const [publish, timing] = useWatch({ control, name: ["publish", "timing"] });
  const now = useNowMinute();
  const timeZone = useTimeZoneName();

  const missing = (["postWindowEnd", "claimDeadline", "proofDeadline"] as const).filter((key) => !timing[key]);
  const canSuggest = Boolean(timing.postWindowStart) && missing.length > 0;

  function suggestTheRest() {
    const suggestion = suggestedTiming(timing.postWindowStart);
    for (const key of missing) setValue(`timing.${key}`, suggestion[key], { shouldDirty: true, shouldValidate: true });
  }

  return (
    <div className="grid gap-5">
      {alreadyDropped && source ? (
        <Callout title={`This campaign is ${campaignStatusMeta[source.status].label.toLowerCase()}`}>
          It&apos;s already out, so there&apos;s nothing to publish. Saving updates it in place, and creators on it get a
          note that the brief changed. You can still move the deadlines.
        </Callout>
      ) : (
        <FieldSection title="How it goes out" description="Publish now, schedule the drop, or keep it as a draft.">
          <Controller
            control={control}
            name="publish"
            render={({ field }) => (
              <ChoiceCards
                ref={field.ref}
                aria-label="How it goes out"
                columns={3}
                value={field.value}
                onChange={field.onChange}
                choices={(["draft", "now", "schedule"] as const).map((value) => ({
                  value,
                  label: publishMeta[value].label,
                  hint: publishMeta[value].hint,
                  icon: publishIcon[value],
                }))}
              />
            )}
          />
          {publish === "schedule" ? (
            <DateTimeField
              name="timing.dropAt"
              label="Drop time"
              hint="When it appears on the board and the notifications go out. Has to be before claiming closes."
            />
          ) : null}
        </FieldSection>
      )}

      <FieldSection
        title="Post window and deadlines"
        description={`In your time zone${timeZone ? ` (${timeZone})` : ""}. Each time is saved in UTC, and creators see it in their own time plus UTC.`}
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <DateTimeField name="timing.postWindowStart" label="Post window opens" hint="The earliest anyone can post." />
          <DateTimeField name="timing.postWindowEnd" label="Post window closes" hint="The latest anyone can post." />
          <DateTimeField
            name="timing.claimDeadline"
            label="Claiming closes"
            hint="The Claim button closes. Before the window ends, ideally before it opens."
          />
          <DateTimeField
            name="timing.proofDeadline"
            label="Proof is due"
            hint="Last moment to paste the post link. At or after the window closes."
          />
        </div>
        {canSuggest ? (
          <div className="flex flex-col gap-3 rounded-lg bg-surface-2/60 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[13px] leading-snug text-muted-foreground">
              Fill the empty times with a typical shape: a 4 hour window, claiming closes 2 hours before it, proof due a
              day after it opens.
            </p>
            <Button type="button" variant="secondary" size="sm" className="shrink-0" onClick={suggestTheRest}>
              <Sparkles aria-hidden />
              Suggest the rest
            </Button>
          </div>
        ) : null}
      </FieldSection>

      <FieldSection title="Timeline" description="Redraws as you change the times.">
        <CampaignTimeline
          drop={alreadyDropped ? "" : publish === "now" ? "now" : publish === "schedule" ? timing.dropAt : ""}
          claimDeadline={timing.claimDeadline}
          postWindowStart={timing.postWindowStart}
          postWindowEnd={timing.postWindowEnd}
          proofDeadline={timing.proofDeadline}
          now={now}
        />
        <div className="flex gap-3 border-t pt-4 text-[13px] leading-relaxed text-muted-foreground">
          <Clock className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            <span className="font-medium text-foreground">Post times per creator come later.</span> After people claim,
            open the campaign and give each creator their own post time inside the window, from the roster. It spreads the
            posts out so they don&apos;t all land at once.
          </p>
        </div>
      </FieldSection>
    </div>
  );
}
