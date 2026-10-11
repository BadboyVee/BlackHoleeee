import { CircleAlert, Info, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

type FormFieldProps = {
  /** The id of the control. The label, hint and error are linked to it. */
  id: string;
  label: React.ReactNode;
  hint?: React.ReactNode;
  error?: string;
  optional?: boolean;
  /** Shown at the end of the label row, e.g. a character count. */
  aside?: React.ReactNode;
  /** Render the label as a legend-like heading for a group (no htmlFor). */
  group?: boolean;
  className?: string;
  children: React.ReactNode;
};

/** The id list a control should point aria-describedby at. */
export function describedBy(id: string, { hint, error }: { hint?: unknown; error?: unknown }) {
  const ids = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean);
  return ids.length ? ids.join(" ") : undefined;
}

/**
 * Label, control, hint and error in one block. Errors sit under the control
 * and are announced; hints stay visible so the rule is always in view.
 */
export function FormField({ id, label, hint, error, optional, aside, group, className, children }: FormFieldProps) {
  const LabelTag = group ? "p" : "label";
  return (
    <div className={cn("grid min-w-0 gap-2", className)}>
      <div className="flex min-h-5 items-baseline justify-between gap-3">
        <LabelTag
          {...(group ? { id: `${id}-label` } : { htmlFor: id })}
          className="text-sm leading-5 font-medium text-foreground"
        >
          {label}
          {optional ? <span className="ml-1.5 text-xs font-normal text-subtle-foreground">Optional</span> : null}
        </LabelTag>
        {aside ? <div className="shrink-0 text-xs text-subtle-foreground">{aside}</div> : null}
      </div>
      {children}
      {error ? (
        <p id={`${id}-error`} role="alert" className="flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={`${id}-hint`} className="text-[13px] leading-snug text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/** "54 / 140", turning to a warning near the limit. */
export function CharCount({ value, max }: { value: string; max: number }) {
  const length = value.length;
  return (
    <span
      className={cn(
        "font-mono text-[11px] tabular",
        length > max ? "font-medium text-destructive-text" : length > max * 0.9 ? "text-(--tone-amber)" : "text-subtle-foreground",
      )}
      aria-live={length > max * 0.9 ? "polite" : undefined}
    >
      {length} / {max}
    </span>
  );
}

const calloutTone = {
  info: { icon: Info, className: "border-border bg-surface-2/50", tone: "blue" },
  warning: { icon: TriangleAlert, className: "border-(--tone-amber)/30 bg-(--tone-amber)/8", tone: "amber" },
  danger: { icon: CircleAlert, className: "border-destructive-text/30 bg-destructive-text/6", tone: "red" },
} as const;

/** A short note in the flow of a form: info, a warning, or a problem. */
export function Callout({
  tone = "info",
  title,
  children,
  className,
  action,
}: {
  tone?: keyof typeof calloutTone;
  title?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  const config = calloutTone[tone];
  const Icon = config.icon;
  return (
    <div
      data-tone={config.tone}
      role={tone === "info" ? undefined : "status"}
      className={cn("flex gap-3 rounded-lg border px-3.5 py-3 text-[13px] leading-relaxed", config.className, className)}
    >
      <Icon className="mt-0.5 size-4 shrink-0 text-(--tone-fg)" aria-hidden />
      <div className="min-w-0 flex-1">
        {title ? <p className="font-medium text-foreground">{title}</p> : null}
        {children ? <div className={cn("text-muted-foreground", title && "mt-0.5")}>{children}</div> : null}
      </div>
      {action ? <div className="shrink-0 self-center">{action}</div> : null}
    </div>
  );
}

/** A titled group of fields inside a builder step. */
export function FieldSection({
  title,
  description,
  children,
  className,
  aside,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  aside?: React.ReactNode;
}) {
  return (
    <section className={cn("rounded-lg border bg-surface p-4 shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)] sm:p-5", className)}>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-[15px] font-semibold tracking-[-0.015em]">{title}</h3>
          {description ? <p className="mt-0.5 text-[13px] leading-snug text-muted-foreground">{description}</p> : null}
        </div>
        {aside}
      </div>
      <div className="grid gap-5">{children}</div>
    </section>
  );
}
