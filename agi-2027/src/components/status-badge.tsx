import { Badge } from "@/components/ui/badge";
import { statusMeta, type StatusKind, type StatusMeta } from "@/lib/statuses";
import { cn } from "@/lib/utils";

type StatusBadgeProps<K extends StatusKind> = {
  kind: K;
  status: keyof (typeof statusMeta)[K] & string;
  className?: string;
};

/** A status as a quiet pill: the label in neutral text, the meaning in a colored dot. */
function StatusBadge<K extends StatusKind>({ kind, status, className }: StatusBadgeProps<K>) {
  const meta = (statusMeta[kind] as Record<string, StatusMeta>)[status];
  return (
    <Badge
      tone={meta.tone}
      variant={meta.attention ? "tone" : "default"}
      className={cn(!meta.attention && "text-foreground/85", className)}
      title={meta.description}
    >
      <StatusDot tone={meta.tone} pulse={meta.pulse} />
      {meta.label}
    </Badge>
  );
}

function StatusDot({
  tone,
  pulse = false,
  className,
}: {
  tone?: StatusMeta["tone"];
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      data-tone={tone}
      className={cn("relative flex size-1.5 shrink-0 text-(--tone-fg)", className)}
    >
      {pulse ? (
        <span className="absolute inset-0 animate-pulse-ring rounded-full bg-current" />
      ) : null}
      <span className="relative size-full rounded-full bg-current" />
    </span>
  );
}

export { StatusBadge, StatusDot };
