import * as React from "react";
import { CircleAlert } from "lucide-react";

import { cn } from "@/lib/utils";
import { Label } from "./label";

type FieldProps = {
  /** The id of the control inside. Used to link the label, hint and error. */
  id: string;
  label: React.ReactNode;
  hint?: React.ReactNode;
  error?: string;
  optional?: boolean;
  className?: string;
  children: React.ReactNode;
};

/**
 * Label, control, hint and error in one block. The control should set
 * aria-describedby={fieldDescribedBy(id, { hint, error })} and
 * aria-invalid when there is an error.
 */
function Field({ id, label, hint, error, optional, className, children }: FieldProps) {
  return (
    <div data-slot="field" className={cn("grid gap-2", className)}>
      <Label htmlFor={id} className="justify-between">
        <span>{label}</span>
        {optional ? (
          <span className="text-xs font-normal text-subtle-foreground">Optional</span>
        ) : null}
      </Label>
      {children}
      {hint && !error ? (
        <p id={`${id}-hint`} className="text-[13px] leading-snug text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p
          id={`${id}-error`}
          role="alert"
          className="flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text"
        >
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : null}
    </div>
  );
}

function fieldDescribedBy(id: string, { hint, error }: { hint?: unknown; error?: unknown }) {
  if (error) return `${id}-error`;
  if (hint) return `${id}-hint`;
  return undefined;
}

export { Field, fieldDescribedBy };
