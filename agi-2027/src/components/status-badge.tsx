import { Badge } from "@/components/ui/badge";
import { statusMeta, type StatusKind, type StatusMeta } from "@/lib/statuses";
import { cn } from "@/lib/utils";

type StatusBadgeProps<K extends StatusKind> = {
  kind: K;
  status: keyof (typeof statusMeta)[K] & string;
  className?: string;
};

function StatusBadge<K extends StatusKind>({ kind, status, className }: StatusBadgeProps<K>) {
  const meta = (statusMeta[kind] as Record<string, StatusMeta>)[status];
  return (
    <Badge tone={meta.tone} className={className} title={meta.description}>
      <StatusDot pulse={meta.pulse} />
      {meta.label}
    </Badge>
  );
}

function StatusDot({ pulse = false, className }: { pulse?: boolean; className?: string }) {
  return (
    <span aria-hidden className={cn("relative flex size-1.5 shrink-0", className)}>
      {pulse ? (
        <span className="absolute inset-0 animate-pulse-ring rounded-full bg-current" />
      ) : null}
      <span className="relative size-1.5 rounded-full bg-current" />
    </span>
  );
}

export { StatusBadge, StatusDot };
