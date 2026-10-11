"use client";

import { useMemo } from "react";
import { Controller, useWatch } from "react-hook-form";
import { CircleAlert, Pencil, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  audienceMeta,
  claimModeMeta,
  CURRENCIES,
  deliverableMeta,
  NEEDS_TARGET_POST,
  platformLabel,
  publishMeta,
} from "@/lib/campaigns/options";
import { clientById, creatorById } from "@/lib/campaigns/demo";
import { formatMoney, totalsByCurrency } from "@/lib/money";
import {
  amountSchema,
  campaignCommitment,
  campaignWarnings,
  makeCampaignSchema,
  type CampaignFormInput,
} from "@/lib/campaigns/schema";
import { cn } from "@/lib/utils";
import { shortLink } from "../../campaign-preview";
import { CharCount, describedBy, FieldSection, FormField } from "../../form-field";
import { Segmented } from "../../segmented";
import { LocalWhen, LocalWindow, utcText, utcWindowText } from "../../time-text";
import { STEPS, stepForPath } from "../form-values";
import { audienceReach } from "./payout";
import { fieldId, useBuilder, useBuilderForm, useFieldError } from "../use-builder";

type Row = { label: string; value: React.ReactNode; missing?: boolean };

function Missing({ children = "Missing" }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 text-destructive-text">
      <CircleAlert className="size-3.5" aria-hidden />
      {children}
    </span>
  );
}

const list = (items: string[]) => (items.length ? items.join(", ") : <span className="text-subtle-foreground">None</span>);

function summaryRows(values: CampaignFormInput, alreadyDropped: boolean): Row[][] {
  const client = clientById(values.clientId);
  const brand =
    values.clientId === "new" ? (
      values.newClient?.name ? (
        `${values.newClient.name} (new brand)`
      ) : (
        <Missing>New brand needs a name</Missing>
      )
    ) : (
      client?.name ?? <Missing />
    );
  const commitment = campaignCommitment({
    payout: values.payout,
    slots: values.slots,
    tierPayouts: values.tierPayouts,
    creatorPayouts: values.creatorPayouts,
  });
  const reach = audienceReach(values.audience);
  const audienceDetail =
    values.audience.kind === "tiers"
      ? values.audience.tiers.join(", ")
      : values.audience.kind === "tags"
        ? values.audience.tags.join(", ")
        : values.audience.kind === "creators"
          ? values.audience.creatorIds.map((id) => creatorById(id)?.name ?? id).join(", ")
          : "";
  const t = values.timing;
  const when = (iso: string) =>
    iso ? (
      <>
        <LocalWhen value={iso} />
        <span className="block text-xs text-subtle-foreground">{utcText(iso)}</span>
      </>
    ) : (
      <Missing />
    );

  return [
    [
      { label: "Brand", value: brand },
      { label: "Title", value: values.title.trim() || <Missing /> },
      { label: "Summary", value: values.summary.trim() || <Missing /> },
      { label: "Post", value: `${deliverableMeta[values.deliverable].label} on ${platformLabel[values.platform]}` },
      ...(NEEDS_TARGET_POST.has(values.deliverable)
        ? [{ label: "Target post", value: values.links.targetPostUrl ? shortLink(values.links.targetPostUrl) : <Missing /> }]
        : []),
      { label: "Tracking link", value: values.links.trackingUrl ? shortLink(values.links.trackingUrl) : <span className="text-subtle-foreground">None</span> },
    ],
    [
      { label: "Key message", value: values.brief.keyMessage.trim() || <Missing /> },
      { label: "About", value: values.brief.about.trim() ? <span className="line-clamp-2">{values.brief.about}</span> : <Missing /> },
      { label: "What to say", value: values.brief.whatToSay.trim() ? <span className="line-clamp-2">{values.brief.whatToSay}</span> : <Missing /> },
      { label: "Do's and don'ts", value: `${values.brief.dos.length} do's, ${values.brief.donts.length} don'ts` },
      { label: "Angles", value: values.angles.length ? `${values.angles.length}: ${values.angles.slice(0, 2).join(", ")}${values.angles.length > 2 ? ", ..." : ""}` : "None yet" },
    ],
    [
      { label: "Mentions", value: list(values.requiredTags.mentions) },
      { label: "Hashtags", value: list(values.requiredTags.hashtags) },
      { label: "Keywords", value: list(values.requiredTags.keywords) },
      { label: "Paid label", value: values.paidLabelRequired ? "Required" : <span className="text-(--tone-amber)" data-tone="amber">Off</span> },
      { label: "Draft first", value: values.draftRequired ? "Yes, you approve each draft" : "No, straight to posting" },
      {
        label: "Assets",
        value: `${values.assets.files.length} ${values.assets.files.length === 1 ? "file" : "files"}${values.assets.brandKitUrl ? " and a brand kit" : ""}`,
      },
    ],
    [
      { label: "Per post", value: values.payout.amount ? formatMoney(values.payout.amount, values.payout.currency) : <Missing /> },
      {
        label: "Custom amounts",
        value:
          values.tierPayouts.length || values.creatorPayouts.length
            ? [
                ...values.tierPayouts.map((row) => `${row.tier}: ${row.amount ? formatMoney(row.amount, values.payout.currency) : "?"}`),
                values.creatorPayouts.length ? `${values.creatorPayouts.length} creator amounts` : "",
              ]
                .filter(Boolean)
                .join(", ")
            : "None",
      },
      { label: "Slots", value: Number.isFinite(values.slots) ? values.slots : <Missing /> },
      {
        label: "Commits",
        value: commitment
          ? commitment.varies
            ? `${formatMoney(commitment.low, commitment.currency)} to ${formatMoney(commitment.high, commitment.currency)}`
            : formatMoney(commitment.base, commitment.currency)
          : <Missing>Needs an amount and slots</Missing>,
      },
      {
        label: "Audience",
        value: (
          <>
            {audienceMeta[values.audience.kind].label}
            {audienceDetail ? `: ${audienceDetail}` : ""}
            <span className="block text-xs text-subtle-foreground">
              {reach.length} {reach.length === 1 ? "creator" : "creators"} can see it
            </span>
          </>
        ),
      },
      { label: "Claim mode", value: claimModeMeta[values.claimMode].label },
    ],
    [
      ...(alreadyDropped
        ? []
        : [
            {
              label: "Goes out",
              value:
                values.publish === "schedule" ? (
                  t.dropAt ? (
                    <>
                      Drops <LocalWhen value={t.dropAt} />
                      <span className="block text-xs text-subtle-foreground">{utcText(t.dropAt)}</span>
                    </>
                  ) : (
                    <Missing>Pick a drop time</Missing>
                  )
                ) : (
                  publishMeta[values.publish].label
                ),
            },
          ]),
      {
        label: "Post window",
        value:
          t.postWindowStart && t.postWindowEnd ? (
            <>
              <LocalWindow start={t.postWindowStart} end={t.postWindowEnd} />
              <span className="block text-xs text-subtle-foreground">{utcWindowText(t.postWindowStart, t.postWindowEnd)}</span>
            </>
          ) : (
            <Missing />
          ),
      },
      { label: "Claiming closes", value: when(t.claimDeadline) },
      { label: "Proof is due", value: when(t.proofDeadline) },
    ],
  ];
}

function BudgetCheck() {
  const { control } = useBuilderForm();
  const [payout, slots, tierPayouts, creatorPayouts, budgetAmount, budgetCurrency] = useWatch({
    control,
    name: ["payout", "slots", "tierPayouts", "creatorPayouts", "internal.budgetAmount", "internal.budgetCurrency"],
  });
  const commitment = campaignCommitment({ payout, slots, tierPayouts, creatorPayouts });
  const budget = budgetAmount?.trim() ?? "";
  if (!budget) {
    return <p className="text-[13px] text-muted-foreground">Add a budget to check the payouts against it.</p>;
  }
  if (!amountSchema.safeParse(budget).success) {
    return <p className="text-[13px] text-muted-foreground">Use a plain number for the budget, like 6000.</p>;
  }
  if (!commitment) {
    return <p className="text-[13px] text-muted-foreground">Set the payout and slots to run the budget check.</p>;
  }
  if (budgetCurrency !== commitment.currency) {
    return (
      <p className="text-[13px] text-(--tone-amber)" data-tone="amber">
        The budget is in {budgetCurrency} and payouts are in {commitment.currency}. Currencies are never converted or added, so
        set both to the same one to compare.
      </p>
    );
  }
  // Exact difference in minor units: highest possible spend minus the budget.
  const difference = totalsByCurrency([
    { amount: commitment.high, currency: commitment.currency },
    { amount: `-${budget}`, currency: commitment.currency },
  ])[0]?.amount ?? "0.00";
  const over = Number(difference) > 0;
  const share = Math.min(1, Number(commitment.high) / Number(budget));
  return (
    <div className="grid gap-2" aria-live="polite">
      <div className="flex items-baseline justify-between gap-3 text-[13px]">
        <span className={cn("font-medium", over ? "text-destructive-text" : "text-foreground")}>
          {over ? "Over budget" : "Within budget"}
        </span>
        <span className="text-muted-foreground tabular">
          {formatMoney(commitment.high, commitment.currency)} of {formatMoney(budget, budgetCurrency)}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-3" role="presentation">
        <div
          className={cn("h-full rounded-full transition-[width] duration-300 ease-spring-smooth", over ? "bg-destructive-text" : "bg-foreground/75")}
          style={{ width: `${Math.round(share * 100)}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        {over
          ? `Paying every slot${commitment.varies ? " at the highest amount" : ""} goes ${formatMoney(difference, budgetCurrency)} over.`
          : `${formatMoney(difference.replace(/^-/, ""), budgetCurrency)} left if every slot is paid${commitment.varies ? " the highest amount" : ""}.`}
      </p>
    </div>
  );
}

export function ReviewStep() {
  const { control, register, setValue } = useBuilderForm();
  const { goTo, alreadyDropped } = useBuilder();
  const values = useWatch({ control }) as CampaignFormInput;
  const notes = useWatch({ control, name: "internal.notes" });
  const budgetError = useFieldError("internal.budgetAmount");
  const groups = summaryRows(values, alreadyDropped);

  const schema = useMemo(() => makeCampaignSchema(undefined, { alreadyDropped }), [alreadyDropped]);
  const parsed = schema.safeParse(values);
  const warnings = parsed.success ? campaignWarnings(parsed.data) : [];
  const problemPaths = parsed.success ? [] : [...new Set(parsed.error.issues.map((issue) => issue.path.join(".")))];
  const problemSteps = [...new Set(problemPaths.map(stepForPath))].sort((a, b) => a - b);
  const problemCount = problemPaths.length;

  return (
    <div className="grid gap-5">
      <FieldSection
        title="Internal"
        description="Only your team sees this. It never reaches creators or the client report."
      >
        <FormField
          id={fieldId("internal.notes")}
          label="Admin notes"
          optional
          hint="Context for whoever runs the campaign: client asks, risks, who approved what."
          aside={<CharCount value={notes ?? ""} max={4000} />}
        >
          <Textarea
            id={fieldId("internal.notes")}
            rows={3}
            className="min-h-24"
            placeholder="Client wants 20 posts inside the first four hours."
            aria-describedby={describedBy(fieldId("internal.notes"), { hint: true })}
            {...register("internal.notes")}
          />
        </FormField>
        <FormField
          id={fieldId("internal.budgetAmount")}
          label="Campaign budget"
          optional
          error={budgetError}
          hint="What the client is paying for creators. Used for the budget check below."
        >
          <Controller
            control={control}
            name="internal.budgetCurrency"
            render={({ field }) => (
              <div className="grid gap-2.5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                <Input
                  id={fieldId("internal.budgetAmount")}
                  inputMode="decimal"
                  placeholder="6000"
                  className="tabular"
                  aria-invalid={budgetError ? true : undefined}
                  aria-describedby={describedBy(fieldId("internal.budgetAmount"), { hint: true, error: budgetError })}
                  {...register("internal.budgetAmount")}
                />
                <Segmented
                  aria-label="Budget currency"
                  size="sm"
                  value={field.value}
                  onChange={(next) => setValue("internal.budgetCurrency", next, { shouldDirty: true })}
                  options={CURRENCIES.map((code) => ({ value: code, label: code }))}
                />
              </div>
            )}
          />
        </FormField>
        <div className="rounded-lg bg-surface-2/50 px-4 py-3">
          <BudgetCheck />
        </div>
      </FieldSection>

      {problemSteps.length ? (
        <div role="status" className="rounded-lg border border-destructive-text/30 bg-destructive-text/6 px-4 py-3">
          <p className="flex items-center gap-2 text-sm font-medium text-destructive-text">
            <CircleAlert className="size-4" aria-hidden />
            {problemCount === 1 ? "One thing to fix" : `${problemCount} things to fix`} before this can go out
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {problemSteps.map((index) => (
              <Button key={index} type="button" variant="secondary" size="sm" onClick={() => goTo(index)}>
                {STEPS[index].title}
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      {warnings.length ? (
        <div className="rounded-lg border border-(--tone-amber)/30 bg-(--tone-amber)/8 px-4 py-3" data-tone="amber">
          <p className="flex items-center gap-2 text-sm font-medium text-foreground">
            <TriangleAlert className="size-4 text-(--tone-fg)" aria-hidden />
            Worth a second look
          </p>
          <ul className="mt-1.5 grid gap-1 pl-6 text-[13px] leading-relaxed text-muted-foreground">
            {warnings.map((warning) => (
              <li key={warning} className="list-disc">
                {warning}
              </li>
            ))}
          </ul>
          <p className="mt-2 pl-6 text-xs text-subtle-foreground">These never block saving.</p>
        </div>
      ) : null}

      <section aria-labelledby="summary-title" className="grid gap-3">
        <div className="flex items-baseline justify-between gap-3">
          <h3 id="summary-title" className="text-[15px] font-semibold tracking-[-0.015em]">
            Summary
          </h3>
          <p className="text-xs text-muted-foreground">Everything creators and your team will see</p>
        </div>
        {groups.map((rows, index) => (
          <div key={STEPS[index].id} className="overflow-hidden rounded-lg border bg-surface">
            <div className="flex items-center justify-between gap-3 border-b bg-surface-2/40 px-4 py-2">
              <p className="text-label text-subtle-foreground">
                {index + 1}. {STEPS[index].title}
              </p>
              <Button type="button" variant="ghost" size="sm" onClick={() => goTo(index)} aria-label={`Edit ${STEPS[index].title}`}>
                <Pencil aria-hidden />
                Edit
              </Button>
            </div>
            <dl className="divide-y">
              {rows.map((row) => (
                <div key={row.label} className="grid gap-0.5 px-4 py-2.5 sm:grid-cols-[9.5rem_minmax(0,1fr)] sm:gap-4">
                  <dt className="text-[13px] text-muted-foreground">{row.label}</dt>
                  <dd className="min-w-0 text-[13px] break-words text-foreground">{row.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </section>
    </div>
  );
}
