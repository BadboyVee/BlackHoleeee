"use client";

import { useState } from "react";
import { Controller, useWatch } from "react-hook-form";
import { Hand, Layers, Search, Tags, Users, Zap } from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  audienceMeta,
  AUDIENCE_KINDS,
  claimModeMeta,
  CREATOR_TAGS,
  CURRENCIES,
  TIERS,
  type AudienceKind,
} from "@/lib/campaigns/options";
import { demoCreators, type DemoCreator } from "@/lib/campaigns/demo";
import { formatMoney } from "@/lib/money";
import { campaignCommitment, type CampaignFormInput } from "@/lib/campaigns/schema";
import { cn } from "@/lib/utils";
import { brandInitials } from "../../brand-tile";
import { ChoiceCards } from "../../choice-cards";
import { Callout, describedBy, FieldSection, FormField } from "../../form-field";
import { NumberStepper } from "../../number-stepper";
import { Segmented } from "../../segmented";
import { fieldId, useBuilderForm, useFieldError } from "../use-builder";

const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

const audienceIcon: Record<AudienceKind, React.ReactNode> = {
  all: <Users className="size-4" />,
  tiers: <Layers className="size-4" />,
  tags: <Tags className="size-4" />,
  creators: <Hand className="size-4" />,
};

/** Who can see the campaign with the audience as set right now. */
export function audienceReach(audience: CampaignFormInput["audience"]): DemoCreator[] {
  return demoCreators.filter((creator) => {
    switch (audience.kind) {
      case "all":
        return true;
      case "tiers":
        return audience.tiers.includes(creator.tier);
      case "tags":
        return audience.tags.some((tag) => creator.tags.includes(tag));
      case "creators":
        return audience.creatorIds.includes(creator.id);
    }
  });
}

function ToggleChip({
  pressed,
  onClick,
  children,
  count,
}: {
  pressed: boolean;
  onClick: () => void;
  children: React.ReactNode;
  count: number;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        "inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-full border px-3.5 text-sm font-medium transition-colors pointer-coarse:min-h-11",
        pressed ? "border-foreground bg-foreground text-background" : "border-border-strong bg-surface hover:bg-surface-2",
      )}
    >
      {children}
      <span className={cn("font-mono text-[11px] tabular", pressed ? "text-background/70" : "text-subtle-foreground")}>{count}</span>
    </button>
  );
}

function Commitment() {
  const { control } = useBuilderForm();
  const [payout, slots, tierPayouts, creatorPayouts] = useWatch({
    control,
    name: ["payout", "slots", "tierPayouts", "creatorPayouts"],
  });
  const commitment = campaignCommitment({ payout, slots, tierPayouts: tierPayouts ?? [], creatorPayouts: creatorPayouts ?? [] });
  if (!commitment) {
    return (
      <p className="rounded-lg border border-dashed px-4 py-3 text-[13px] text-muted-foreground">
        Add an amount and the number of slots to see what the campaign commits you to.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 rounded-lg bg-surface-2/60 px-4 py-3" aria-live="polite">
      <p className="text-[13px] text-muted-foreground">
        {formatMoney(payout.amount, payout.currency)} × {slots} {slots === 1 ? "slot" : "slots"}
        {commitment.varies ? ", with custom amounts" : ""}
      </p>
      <p className="text-right">
        <span className="text-xs text-muted-foreground">{commitment.varies ? "Commits between " : "Commits "}</span>
        <span className="text-figure text-lg">
          {commitment.varies
            ? `${formatMoney(commitment.low, commitment.currency)} and ${formatMoney(commitment.high, commitment.currency)}`
            : formatMoney(commitment.base, commitment.currency)}
        </span>
      </p>
    </div>
  );
}

function TierRates() {
  const { control } = useBuilderForm();
  const base = useWatch({ control, name: "payout.amount" });
  const currency = useWatch({ control, name: "payout.currency" });
  const tierError = useFieldError("tierPayouts");
  return (
    <Controller
      control={control}
      name="tierPayouts"
      render={({ field, formState }) => {
        const rows = field.value ?? [];
        return (
          <FormField
            id={fieldId("tierPayouts")}
            label="Custom amount per tier"
            group
            optional
            error={tierError}
            hint="Pay a tier more or less than the base amount. A hand-picked creator's own amount beats their tier's."
          >
            <ul className="divide-y rounded-lg border" aria-labelledby={`${fieldId("tierPayouts")}-label`}>
              {TIERS.map((tier) => {
                const index = rows.findIndex((row) => row.tier === tier);
                const on = index !== -1;
                const rowError = on ? formState.errors.tierPayouts?.[index]?.amount?.message : undefined;
                const inputId = fieldId(`tierPayouts.${tier}`);
                const count = demoCreators.filter((creator) => creator.tier === tier).length;
                return (
                  <li key={tier} className="grid gap-2 px-3.5 py-3 sm:grid-cols-[minmax(0,1fr)_12rem] sm:items-center">
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={on}
                        aria-label={`Custom amount for ${tier}`}
                        onCheckedChange={(checked) =>
                          field.onChange(checked ? [...rows, { tier, amount: "" }] : rows.filter((row) => row.tier !== tier))
                        }
                      />
                      <span className="text-sm font-medium">{tier}</span>
                      <span className="text-xs text-muted-foreground">{count} creators</span>
                    </div>
                    {on ? (
                      <div className="grid gap-1">
                        <div className="relative">
                          <Input
                            id={inputId}
                            inputMode="decimal"
                            value={rows[index]?.amount ?? ""}
                            onChange={(event) =>
                              field.onChange(rows.map((row) => (row.tier === tier ? { ...row, amount: event.target.value } : row)))
                            }
                            placeholder={base || "0"}
                            aria-label={`${tier} amount in ${currency}`}
                            aria-invalid={rowError ? true : undefined}
                            className="h-10 pr-16 tabular"
                          />
                          <span className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 font-mono text-xs text-muted-foreground">
                            {currency}
                          </span>
                        </div>
                        {rowError ? <p className="text-xs text-destructive-text">{rowError}</p> : null}
                      </div>
                    ) : (
                      <p className="text-[13px] text-subtle-foreground sm:text-right">Base amount</p>
                    )}
                  </li>
                );
              })}
            </ul>
          </FormField>
        );
      }}
    />
  );
}

function CreatorPicker() {
  const { control, setValue, getValues, formState } = useBuilderForm();
  const [query, setQuery] = useState("");
  const [creatorIds, creatorPayouts, base, currency] = useWatch({
    control,
    name: ["audience.creatorIds", "creatorPayouts", "payout.amount", "payout.currency"],
  });
  const error = useFieldError("audience.creatorIds");
  const shown = demoCreators.filter((creator) =>
    `${creator.name} ${creator.handle} ${creator.tier} ${creator.tags.join(" ")}`.toLowerCase().includes(query.trim().toLowerCase()),
  );

  function toggle(id: string, on: boolean) {
    const ids = getValues("audience.creatorIds");
    setValue("audience.creatorIds", on ? [...ids, id] : ids.filter((entry) => entry !== id), { shouldDirty: true, shouldValidate: true });
    if (!on) setValue("creatorPayouts", getValues("creatorPayouts").filter((row) => row.creatorId !== id), { shouldDirty: true });
  }

  function setAmount(id: string, amount: string) {
    const rows = getValues("creatorPayouts");
    const next = amount.trim()
      ? rows.some((row) => row.creatorId === id)
        ? rows.map((row) => (row.creatorId === id ? { ...row, amount } : row))
        : [...rows, { creatorId: id, amount }]
      : rows.filter((row) => row.creatorId !== id);
    setValue("creatorPayouts", next, { shouldDirty: true });
  }

  return (
    <FormField
      id={fieldId("audience.creatorIds")}
      label={`Hand-picked creators (${creatorIds.length} chosen)`}
      group
      error={error}
      hint="Only these creators see the campaign. Add a custom amount to pay someone more or less than the base."
    >
      <div className="rounded-lg border">
        <label className="relative block border-b">
          <span className="sr-only">Search creators</span>
          <Search aria-hidden className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-subtle-foreground" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by name, handle, tier or tag"
            className="h-11 w-full rounded-t-lg bg-transparent pr-3 pl-10 text-base outline-none placeholder:text-subtle-foreground focus-visible:bg-surface-2/40 sm:text-sm"
          />
        </label>
        <ul className="max-h-[22rem] divide-y overflow-y-auto" aria-labelledby={`${fieldId("audience.creatorIds")}-label`}>
          {shown.map((creator) => {
            const checked = creatorIds.includes(creator.id);
            const rowIndex = creatorPayouts.findIndex((row) => row.creatorId === creator.id);
            const amount = rowIndex === -1 ? "" : creatorPayouts[rowIndex].amount;
            const amountError = rowIndex === -1 ? undefined : formState.errors.creatorPayouts?.[rowIndex]?.amount?.message;
            const checkboxId = `pick-${creator.id}`;
            return (
              <li key={creator.id} className={cn("grid gap-2 px-3.5 py-2.5 sm:grid-cols-[minmax(0,1fr)_10.5rem] sm:items-center", checked && "bg-surface-2/40")}>
                <div className="flex min-w-0 items-center gap-3">
                  <Checkbox id={checkboxId} checked={checked} onCheckedChange={(value) => toggle(creator.id, value === true)} />
                  <label htmlFor={checkboxId} className="flex min-w-0 flex-1 cursor-pointer items-center gap-3">
                    <span
                      aria-hidden
                      className="flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-3 font-mono text-[10px] font-medium text-muted-foreground"
                    >
                      {brandInitials(creator.name)}
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium">{creator.name}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {creator.handle} · {creator.tier} · {compact.format(creator.followers)} followers
                      </span>
                    </span>
                  </label>
                </div>
                {checked ? (
                  <div className="grid gap-1 pl-8 sm:pl-0">
                    <div className="relative">
                      <Input
                        inputMode="decimal"
                        value={amount}
                        onChange={(event) => setAmount(creator.id, event.target.value)}
                        placeholder={base ? `${base} (base)` : "Base"}
                        aria-label={`Custom amount for ${creator.name} in ${currency}`}
                        aria-invalid={amountError ? true : undefined}
                        className="h-10 pr-14 tabular"
                      />
                      <span className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 font-mono text-[11px] text-muted-foreground">
                        {currency}
                      </span>
                    </div>
                    {amountError ? <p className="text-xs text-destructive-text">{amountError}</p> : null}
                  </div>
                ) : null}
              </li>
            );
          })}
          {shown.length === 0 ? <li className="px-4 py-6 text-center text-sm text-muted-foreground">No creators match.</li> : null}
        </ul>
      </div>
    </FormField>
  );
}

export function PayoutStep() {
  const { control, register, setValue, getValues, clearErrors } = useBuilderForm();
  const audience = useWatch({ control, name: "audience" });
  const slots = useWatch({ control, name: "slots" });
  const amountError = useFieldError("payout.amount");
  const slotsError = useFieldError("slots");
  const tiersError = useFieldError("audience.tiers");
  const tagsError = useFieldError("audience.tags");
  const reach = audienceReach(audience);

  return (
    <div className="grid gap-5">
      <FieldSection title="Payout" description="What each approved post earns. Totals are kept per currency, never mixed.">
        <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto]">
          <FormField
            id={fieldId("payout.amount")}
            label="Amount per creator"
            error={amountError}
            hint="Exact amounts only, like 250 or 99.50."
          >
            <Controller
              control={control}
              name="payout.currency"
              render={({ field }) => (
                <div className="grid gap-2.5">
                  <Input
                    id={fieldId("payout.amount")}
                    inputMode="decimal"
                    placeholder="250"
                    className="h-12 text-lg font-semibold tabular"
                    aria-invalid={amountError ? true : undefined}
                    aria-describedby={describedBy(fieldId("payout.amount"), { hint: true, error: amountError })}
                    {...register("payout.amount")}
                  />
                  <Segmented
                    aria-label="Currency"
                    value={field.value}
                    onChange={(next) => {
                      field.onChange(next);
                      // Keep the budget in the same currency until someone sets it.
                      if (!getValues("internal.budgetAmount")) setValue("internal.budgetCurrency", next);
                    }}
                    options={CURRENCIES.map((code) => ({ value: code, label: code }))}
                  />
                </div>
              )}
            />
          </FormField>
          <Controller
            control={control}
            name="slots"
            render={({ field }) => (
              <FormField id={fieldId("slots")} label="Slots" error={slotsError} hint="How many creators can take part.">
                <NumberStepper
                  id={fieldId("slots")}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  inputRef={field.ref}
                  min={1}
                  max={1000}
                  invalid={Boolean(slotsError)}
                  aria-describedby={describedBy(fieldId("slots"), { hint: true, error: slotsError })}
                />
              </FormField>
            )}
          />
        </div>
        <Commitment />
        <TierRates />
      </FieldSection>

      <FieldSection
        title="Audience"
        description="Who sees the campaign on their board. Everyone else never knows it exists."
        aside={
          <span className="shrink-0 rounded-full border bg-surface-2/60 px-2.5 py-1 text-xs font-medium tabular" aria-live="polite">
            {reach.length} of {demoCreators.length} creators
          </span>
        }
      >
        <Controller
          control={control}
          name="audience.kind"
          render={({ field }) => (
            <ChoiceCards
              ref={field.ref}
              aria-label="Audience"
              value={field.value}
              onChange={(next) => {
                field.onChange(next);
                if (next !== "creators") setValue("creatorPayouts", [], { shouldDirty: true });
                clearErrors(["audience.tiers", "audience.tags", "audience.creatorIds"]);
              }}
              choices={AUDIENCE_KINDS.map((kind) => ({
                value: kind,
                label: audienceMeta[kind].label,
                hint: audienceMeta[kind].hint,
                icon: audienceIcon[kind],
              }))}
            />
          )}
        />

        {audience.kind === "tiers" ? (
          <FormField id={fieldId("audience.tiers")} label="Tiers" group error={tiersError}>
            <div className="flex flex-wrap gap-2" role="group" aria-labelledby={`${fieldId("audience.tiers")}-label`}>
              {TIERS.map((tier) => {
                const pressed = audience.tiers.includes(tier);
                return (
                  <ToggleChip
                    key={tier}
                    pressed={pressed}
                    count={demoCreators.filter((creator) => creator.tier === tier).length}
                    onClick={() =>
                      setValue("audience.tiers", pressed ? audience.tiers.filter((entry) => entry !== tier) : [...audience.tiers, tier], {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    }
                  >
                    {tier}
                  </ToggleChip>
                );
              })}
            </div>
          </FormField>
        ) : null}

        {audience.kind === "tags" ? (
          <FormField
            id={fieldId("audience.tags")}
            label="Tags"
            group
            error={tagsError}
            hint="Creators with at least one of these tags see it. Tags are set on each creator's profile."
          >
            <div className="flex flex-wrap gap-2" role="group" aria-labelledby={`${fieldId("audience.tags")}-label`}>
              {CREATOR_TAGS.map((tag) => {
                const pressed = audience.tags.includes(tag);
                return (
                  <ToggleChip
                    key={tag}
                    pressed={pressed}
                    count={demoCreators.filter((creator) => creator.tags.includes(tag)).length}
                    onClick={() =>
                      setValue("audience.tags", pressed ? audience.tags.filter((entry) => entry !== tag) : [...audience.tags, tag], {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    }
                  >
                    {tag}
                  </ToggleChip>
                );
              })}
            </div>
          </FormField>
        ) : null}

        {audience.kind === "creators" ? <CreatorPicker /> : null}

        {audience.kind === "creators" && Number.isFinite(slots) && slots > audience.creatorIds.length && audience.creatorIds.length > 0 ? (
          <Callout tone="warning">
            {slots} slots but {audience.creatorIds.length} hand-picked {audience.creatorIds.length === 1 ? "creator" : "creators"}, so some slots
            can&apos;t be filled. Lower the slots or pick more people.
          </Callout>
        ) : null}
      </FieldSection>

      <FieldSection title="Claim mode" description="What happens when a creator taps Claim.">
        <Controller
          control={control}
          name="claimMode"
          render={({ field }) => (
            <ChoiceCards
              ref={field.ref}
              aria-label="Claim mode"
              value={field.value}
              onChange={field.onChange}
              choices={[
                { value: "instant", label: claimModeMeta.instant.label, hint: claimModeMeta.instant.hint, icon: <Zap className="size-4" /> },
                { value: "apply", label: claimModeMeta.apply.label, hint: claimModeMeta.apply.hint, icon: <Hand className="size-4" /> },
              ]}
            />
          )}
        />
        <p className="text-[13px] leading-relaxed text-muted-foreground">
          Either way, a campaign can never be overfilled. Slots are counted inside the database the moment someone claims,
          so if 40 people tap at once on 10 slots, exactly 10 get in.
        </p>
      </FieldSection>
    </div>
  );
}
