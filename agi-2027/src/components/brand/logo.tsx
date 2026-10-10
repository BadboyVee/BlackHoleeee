import { cn } from "@/lib/utils";

/** The AGI 2027 mark: a four-point spark on an acid lime tile. */
function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden className={cn("size-7 shrink-0", className)}>
      <rect width="32" height="32" rx="9" fill="var(--brand)" />
      <path
        d="M16 7c.7 5.6 3.4 8.3 9 9-5.6.7-8.3 3.4-9 9-.7-5.6-3.4-8.3-9-9 5.6-.7 8.3-3.4 9-9Z"
        fill="var(--brand-foreground)"
      />
    </svg>
  );
}

/** Mark plus the mono wordmark. Set compact to show the mark only. */
function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {compact ? (
        <span className="sr-only">AGI 2027</span>
      ) : (
        <span className="font-mono text-[15px] font-semibold tracking-[-0.02em] whitespace-nowrap">
          AGI<span className="text-muted-foreground"> 2027</span>
        </span>
      )}
    </span>
  );
}

export { Logo, LogoMark };
