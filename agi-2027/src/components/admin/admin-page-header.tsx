import { cn } from "@/lib/utils";

/** Page titles take the active look's display face, weight, tracking and case. */
export const adminTitleClass =
  "font-display text-[calc(1.5rem*var(--display-scale))] leading-[1.08] [font-weight:var(--display-weight)] [letter-spacing:calc(var(--display-tracking)*0.6)] [text-transform:var(--display-case)] sm:text-[calc(1.75rem*var(--display-scale))]";

type AdminPageHeaderProps = {
  title: React.ReactNode;
  description?: React.ReactNode;
  /** Small line above the title, such as the brand a campaign belongs to. */
  eyebrow?: React.ReactNode;
  actions?: React.ReactNode;
  /** Sits before the title, such as a brand tile. */
  leading?: React.ReactNode;
  className?: string;
};

/**
 * The owner screens' page header: compact and quiet. The title takes the
 * active look's display face; everything else stays in the sans.
 */
function AdminPageHeader({ title, description, eyebrow, actions, leading, className }: AdminPageHeaderProps) {
  return (
    <header className={cn("mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between lg:mb-8", className)}>
      <div className="flex min-w-0 items-start gap-3.5">
        {leading}
        <div className="min-w-0">
          {eyebrow ? <div className="mb-1.5 text-[13px] text-muted-foreground">{eyebrow}</div> : null}
          <h1 className={cn(adminTitleClass, "text-balance")}>{title}</h1>
          {description ? (
            <p className="mt-1.5 max-w-2xl text-[15px] leading-relaxed text-pretty text-muted-foreground">{description}</p>
          ) : null}
        </div>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export { AdminPageHeader };
