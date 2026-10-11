"use client";

import { Controller, useWatch } from "react-hook-form";
import { ImagePlus, ListOrdered, MessageSquareQuote, PenLine, Reply, Shapes, Video } from "lucide-react";

import { Input } from "@/components/ui/input";
import { DELIVERABLES, deliverableMeta, NEEDS_TARGET_POST, PLATFORMS, platformLabel, type Deliverable } from "@/lib/campaigns/options";
import { ChoiceCards } from "../../choice-cards";
import { ClientPicker } from "../../client-picker";
import { Callout, CharCount, describedBy, FieldSection, FormField } from "../../form-field";
import { PlatformIcon } from "../../platform-icon";
import { Segmented } from "../../segmented";
import { fieldId, useBuilderForm, useFieldError } from "../use-builder";

const deliverableIcon: Record<Deliverable, React.ReactNode> = {
  original: <PenLine className="size-4" />,
  quote: <MessageSquareQuote className="size-4" />,
  reply: <Reply className="size-4" />,
  thread: <ListOrdered className="size-4" />,
  video: <Video className="size-4" />,
  other: <Shapes className="size-4" />,
};

function NewBrandFields() {
  const { register } = useBuilderForm();
  const nameError = useFieldError("newClient.name");
  const websiteError = useFieldError("newClient.website");
  const handleError = useFieldError("newClient.xHandle");
  return (
    <div className="grid gap-4 rounded-lg border border-dashed border-border-strong bg-surface-2/30 p-4">
      <div className="flex items-start gap-4">
        <div className="grid shrink-0 justify-items-center gap-1.5">
          <span className="flex size-16 items-center justify-center rounded-[30%] border border-dashed border-border-strong bg-surface text-subtle-foreground">
            <ImagePlus className="size-5" aria-hidden />
          </span>
          <span className="max-w-20 text-center text-[11px] leading-tight text-subtle-foreground">Logo upload in Milestone 5</span>
        </div>
        <FormField id={fieldId("newClient.name")} label="Brand name" error={nameError} className="flex-1">
          <Input
            id={fieldId("newClient.name")}
            autoComplete="organization"
            placeholder="Parallax"
            aria-invalid={nameError ? true : undefined}
            aria-describedby={describedBy(fieldId("newClient.name"), { error: nameError })}
            {...register("newClient.name")}
          />
        </FormField>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField id={fieldId("newClient.website")} label="Website" optional error={websiteError}>
          <Input
            id={fieldId("newClient.website")}
            type="url"
            inputMode="url"
            placeholder="https://parallax.example"
            aria-invalid={websiteError ? true : undefined}
            aria-describedby={describedBy(fieldId("newClient.website"), { error: websiteError })}
            {...register("newClient.website")}
          />
        </FormField>
        <FormField id={fieldId("newClient.xHandle")} label="X handle" optional error={handleError}>
          <Input
            id={fieldId("newClient.xHandle")}
            placeholder="@parallax"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            aria-invalid={handleError ? true : undefined}
            aria-describedby={describedBy(fieldId("newClient.xHandle"), { error: handleError })}
            {...register("newClient.xHandle")}
          />
        </FormField>
      </div>
      <p className="text-xs text-muted-foreground">
        The brand is saved to Clients with this campaign, so next time it&apos;s one tap.
      </p>
    </div>
  );
}

export function BasicsStep() {
  const { control, register, setValue, getValues, clearErrors } = useBuilderForm();
  const [clientId, deliverable, title, summary, newBrandName] = useWatch({
    control,
    name: ["clientId", "deliverable", "title", "summary", "newClient.name"],
  });
  const clientError = useFieldError("clientId");
  const titleError = useFieldError("title");
  const summaryError = useFieldError("summary");
  const targetError = useFieldError("links.targetPostUrl");
  const trackingError = useFieldError("links.trackingUrl");
  const needsTarget = NEEDS_TARGET_POST.has(deliverable);

  return (
    <div className="grid gap-5">
      <FieldSection title="Brand" description="Who the campaign is for. Creators see the name and logo on the card.">
        <Controller
          control={control}
          name="clientId"
          render={({ field }) => (
            <FormField id={fieldId("clientId")} label="Brand" error={clientError}>
              <ClientPicker
                id={fieldId("clientId")}
                value={field.value}
                newBrandName={newBrandName}
                triggerRef={field.ref}
                invalid={Boolean(clientError)}
                aria-describedby={describedBy(fieldId("clientId"), { error: clientError })}
                onChange={(next, typedName) => {
                  field.onChange(next);
                  if (next === "new") {
                    if (!getValues("newClient")) {
                      setValue("newClient", { name: typedName ?? "", website: "", xHandle: "" }, { shouldDirty: true });
                    } else if (typedName) {
                      setValue("newClient.name", typedName, { shouldDirty: true });
                    }
                  } else {
                    setValue("newClient", undefined, { shouldDirty: true });
                    clearErrors("newClient");
                  }
                  if (clientError) clearErrors("clientId");
                }}
              />
            </FormField>
          )}
        />
        {clientId === "new" ? <NewBrandFields /> : null}
      </FieldSection>

      <FieldSection title="Title and summary" description="The first two lines creators read on the campaign board.">
        <FormField
          id={fieldId("title")}
          label="Title"
          error={titleError}
          hint="Clear beats clever. Name the launch, not the task."
          aside={<CharCount value={title ?? ""} max={80} />}
        >
          <Input
            id={fieldId("title")}
            placeholder="Nebula 2.0 launch day"
            aria-invalid={titleError ? true : undefined}
            aria-describedby={describedBy(fieldId("title"), { hint: true, error: titleError })}
            {...register("title")}
          />
        </FormField>
        <FormField
          id={fieldId("summary")}
          label="One-line summary"
          error={summaryError}
          hint="What creators will post, in one line. It shows under the title."
          aside={<CharCount value={summary ?? ""} max={140} />}
        >
          <Input
            id={fieldId("summary")}
            placeholder="Quote the launch post with your honest first take on the new agent builder."
            aria-invalid={summaryError ? true : undefined}
            aria-describedby={describedBy(fieldId("summary"), { hint: true, error: summaryError })}
            {...register("summary")}
          />
        </FormField>
      </FieldSection>

      <FieldSection title="Platform and deliverable" description="Where the post goes and what kind of post it is.">
        <Controller
          control={control}
          name="platform"
          render={({ field }) => (
            <FormField
              id={fieldId("platform")}
              label="Platform"
              group
              hint={
                field.value === "x"
                  ? "X gets the free proof checks: the link, the handle and the post itself."
                  : `${platformLabel[field.value]} posts are checked by hand for now. Automatic checks start with X.`
              }
            >
              <Segmented
                id={fieldId("platform")}
                aria-labelledby={`${fieldId("platform")}-label`}
                value={field.value}
                onChange={field.onChange}
                options={PLATFORMS.map((platform) => ({
                  value: platform,
                  label: platformLabel[platform],
                  icon: <PlatformIcon platform={platform} className="size-3.5" />,
                }))}
              />
            </FormField>
          )}
        />
        <Controller
          control={control}
          name="deliverable"
          render={({ field }) => (
            <FormField id={fieldId("deliverable")} label="Deliverable" group>
              <ChoiceCards
                ref={field.ref}
                aria-labelledby={`${fieldId("deliverable")}-label`}
                columns={3}
                value={field.value}
                onChange={(next) => {
                  field.onChange(next);
                  if (!NEEDS_TARGET_POST.has(next)) clearErrors("links.targetPostUrl");
                }}
                choices={DELIVERABLES.map((value) => ({
                  value,
                  label: deliverableMeta[value].label,
                  hint: deliverableMeta[value].hint,
                  icon: deliverableIcon[value],
                }))}
              />
            </FormField>
          )}
        />
        {needsTarget ? (
          <FormField
            id={fieldId("links.targetPostUrl")}
            label={deliverable === "quote" ? "Post to quote" : "Post to reply to"}
            error={targetError}
            hint="Paste the full link, like https://x.com/brand/status/1975000000000000001."
          >
            <Input
              id={fieldId("links.targetPostUrl")}
              type="url"
              inputMode="url"
              placeholder="https://x.com/brand/status/..."
              aria-invalid={targetError ? true : undefined}
              aria-describedby={describedBy(fieldId("links.targetPostUrl"), { hint: true, error: targetError })}
              {...register("links.targetPostUrl")}
            />
          </FormField>
        ) : null}
        <FormField
          id={fieldId("links.trackingUrl")}
          label="Tracking or referral link"
          optional
          error={trackingError}
          hint="If you add one, every creator has to include it in their post."
        >
          <Input
            id={fieldId("links.trackingUrl")}
            type="url"
            inputMode="url"
            placeholder="https://brand.example/?ref=agi2027"
            aria-invalid={trackingError ? true : undefined}
            aria-describedby={describedBy(fieldId("links.trackingUrl"), { hint: true, error: trackingError })}
            {...register("links.trackingUrl")}
          />
        </FormField>
        {deliverable === "other" ? (
          <Callout title="Explain the deliverable in the brief">
            Creators only see &ldquo;Other&rdquo; on the card, so say exactly what you want on the next step.
          </Callout>
        ) : null}
      </FieldSection>
    </div>
  );
}
