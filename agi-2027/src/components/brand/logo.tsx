import { cn } from "@/lib/utils";

/** The AGI 2027 mark: a four-point spark, in the current text color. */
function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden className={cn("size-[18px] shrink-0", className)}>
      <path
        d="M12 1.5c.55 6.15 4.35 9.95 10.5 10.5-6.15.55-9.95 4.35-10.5 10.5-.55-6.15-4.35-9.95-10.5-10.5 6.15-.55 9.95-4.35 10.5-10.5Z"
        fill="currentColor"
      />
    </svg>
  );
}

/** Mark plus the mono wordmark. Set compact to show the mark only. */
function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 text-foreground", className)}>
      <LogoMark />
      {compact ? (
        <span className="sr-only">AGI 2027</span>
      ) : (
        <span className="font-mono text-[14px] font-semibold tracking-[-0.03em] whitespace-nowrap">
          AGI 2027
        </span>
      )}
    </span>
  );
}

export { Logo, LogoMark };
