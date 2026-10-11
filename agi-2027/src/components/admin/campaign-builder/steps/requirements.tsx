"use client";

import { Controller, useWatch } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { handleSchema, hashtagSchema } from "@/lib/campaigns/schema";
import { FileDropZone } from "../../file-drop-zone";
import { Callout, describedBy, FieldSection, FormField } from "../../form-field";
import { TagInput, type TagParser } from "../../tag-input";
import { fieldId, useBuilderForm, useFieldError } from "../use-builder";

const parseHandle: TagParser = (raw) => {
  const result = handleSchema.safeParse(raw);
  return result.success ? { ok: true, value: result.data } : { ok: false, error: result.error.issues[0]?.message ?? "Not a valid handle" };
};

const parseHashtag: TagParser = (raw) => {
  const result = hashtagSchema.safeParse(raw);
  return result.success ? { ok: true, value: result.data } : { ok: false, error: result.error.issues[0]?.message ?? "Not a valid hashtag" };
};

const parseKeyword: TagParser = (raw) => {
  const value = raw.trim().replace(/^["']|["']$/g, "");
  if (!value) return { ok: false, error: "Can't be empty" };
  if (value.length > 60) return { ok: false, error: "Keep it under 60 characters" };
  return { ok: true, value };
};

function RuleSwitch({
  id,
  title,
  description,
  checked,
  onCheckedChange,
}: {
  id: string;
  title: string;
  description: React.ReactNode;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <label htmlFor={id} className="cursor-pointer text-sm font-medium">
          {title}
        </label>
        <p id={`${id}-description`} className="mt-0.5 text-[13px] leading-snug text-muted-foreground">
          {description}
        </p>
      </div>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        aria-describedby={`${id}-description`}
        className="mt-0.5"
      />
    </div>
  );
}

export function RequirementsStep() {
  const { control, register } = useBuilderForm();
  const paidLabel = useWatch({ control, name: "paidLabelRequired" });
  const brandKitError = useFieldError("assets.brandKitUrl");

  return (
    <div className="grid gap-5">
      <FieldSection title="Must appear in every post" description="Free checks look for these when proof comes in, on X.">
        <Controller
          control={control}
          name="requiredTags.mentions"
          render={({ field, fieldState }) => (
            <FormField
              id={fieldId("requiredTags.mentions")}
              label="Mentions"
              optional
              error={fieldState.error?.message}
              hint="Accounts to tag. Type a handle and press Enter or a comma."
            >
              <TagInput
                id={fieldId("requiredTags.mentions")}
                value={field.value ?? []}
                onChange={field.onChange}
                onBlur={field.onBlur}
                inputRef={field.ref}
                parse={parseHandle}
                placeholder="@brand"
                invalid={Boolean(fieldState.error)}
                aria-describedby={describedBy(fieldId("requiredTags.mentions"), { hint: true, error: fieldState.error })}
              />
            </FormField>
          )}
        />
        <Controller
          control={control}
          name="requiredTags.hashtags"
          render={({ field, fieldState }) => (
            <FormField
              id={fieldId("requiredTags.hashtags")}
              label="Hashtags"
              optional
              error={fieldState.error?.message}
              hint="Letters, numbers and underscores. The # is added for you."
            >
              <TagInput
                id={fieldId("requiredTags.hashtags")}
                value={field.value ?? []}
                onChange={field.onChange}
                onBlur={field.onBlur}
                inputRef={field.ref}
                parse={parseHashtag}
                placeholder="#LaunchDay"
                invalid={Boolean(fieldState.error)}
                aria-describedby={describedBy(fieldId("requiredTags.hashtags"), { hint: true, error: fieldState.error })}
              />
            </FormField>
          )}
        />
        <Controller
          control={control}
          name="requiredTags.keywords"
          render={({ field, fieldState }) => (
            <FormField
              id={fieldId("requiredTags.keywords")}
              label="Keywords"
              optional
              error={fieldState.error?.message}
              hint="Words or short phrases the post has to contain, like a product name."
            >
              <TagInput
                id={fieldId("requiredTags.keywords")}
                value={field.value ?? []}
                onChange={field.onChange}
                onBlur={field.onBlur}
                inputRef={field.ref}
                parse={parseKeyword}
                placeholder="agent builder"
                invalid={Boolean(fieldState.error)}
                aria-describedby={describedBy(fieldId("requiredTags.keywords"), { hint: true, error: fieldState.error })}
              />
            </FormField>
          )}
        />
      </FieldSection>

      <FieldSection title="Rules" description="How creators have to post.">
        <Controller
          control={control}
          name="paidLabelRequired"
          render={({ field }) => (
            <RuleSwitch
              id={fieldId("paidLabelRequired")}
              title="Paid partnership label"
              description="Creators must turn on X's paid partnership label and confirm it when they send proof."
              checked={field.value}
              onCheckedChange={field.onChange}
            />
          )}
        />
        {!paidLabel ? (
          <Callout tone="warning" title="Only turn this off for unpaid posts">
            X requires the label on paid posts. Leave it on unless creators aren&apos;t being paid for this one.
          </Callout>
        ) : null}
        <div className="border-t pt-5">
          <Controller
            control={control}
            name="draftRequired"
            render={({ field }) => (
              <RuleSwitch
                id={fieldId("draftRequired")}
                title="Draft required"
                description="Creators send their post as a draft first. You approve it or ask for changes, then they post."
                checked={field.value}
                onCheckedChange={field.onChange}
              />
            )}
          />
        </div>
      </FieldSection>

      <FieldSection title="Assets" description="Images, clips and documents creators can download from the brief.">
        <Controller
          control={control}
          name="assets.files"
          render={({ field }) => <FileDropZone files={field.value ?? []} onChange={field.onChange} />}
        />
        <FormField
          id={fieldId("assets.brandKitUrl")}
          label="Brand kit link"
          optional
          error={brandKitError}
          hint="A folder with logos, colors and screenshots, if the brand has one."
        >
          <Input
            id={fieldId("assets.brandKitUrl")}
            type="url"
            inputMode="url"
            placeholder="https://brand.example/press"
            aria-invalid={brandKitError ? true : undefined}
            aria-describedby={describedBy(fieldId("assets.brandKitUrl"), { hint: true, error: brandKitError })}
            {...register("assets.brandKitUrl")}
          />
        </FormField>
      </FieldSection>
    </div>
  );
}
