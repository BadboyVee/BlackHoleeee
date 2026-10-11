"use client";

import { Controller, useFormContext, type FieldPath } from "react-hook-form";
import { Globe2 } from "lucide-react";

import { fieldControlClass } from "@/components/ui/input";
import type { CampaignFormInput } from "@/lib/campaigns/schema";
import { cn } from "@/lib/utils";
import { isoToLocalInput, localInputToIso } from "./campaign-builder/form-values";
import { describedBy, FormField } from "./form-field";
import { utcText } from "./time-text";

type DateTimeFieldProps = {
  name: FieldPath<CampaignFormInput>;
  label: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
};

/**
 * A date and time in the owner's own time zone, stored as UTC. The UTC value
 * sits right under the field so there's never a doubt which clock it means.
 */
export function DateTimeField({ name, label, hint, className }: DateTimeFieldProps) {
  const { control } = useFormContext<CampaignFormInput>();
  const id = `field-${name.replace(/\./g, "-")}`;
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const value = typeof field.value === "string" ? field.value : "";
        const error = fieldState.error?.message;
        return (
          <FormField id={id} label={label} hint={hint} error={error} className={className}>
            <div className="grid gap-1.5">
              <input
                ref={field.ref}
                id={id}
                name={field.name}
                type="datetime-local"
                value={isoToLocalInput(value)}
                onChange={(event) => field.onChange(localInputToIso(event.target.value))}
                onBlur={field.onBlur}
                aria-invalid={error ? true : undefined}
                aria-describedby={[describedBy(id, { hint, error }), `${id}-utc`].filter(Boolean).join(" ")}
                className={cn(fieldControlClass, "h-11 px-3.5 tabular [color-scheme:inherit]")}
              />
              <p id={`${id}-utc`} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Globe2 className="size-3.5 shrink-0" aria-hidden />
                {value ? utcText(value) : "Shown in UTC once it's set"}
              </p>
            </div>
          </FormField>
        );
      }}
    />
  );
}
