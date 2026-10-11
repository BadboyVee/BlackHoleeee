import { cn } from "@/lib/utils";

/** The active look's display face, weight, tracking and case, for headings. */
export const displayType =
  "font-display [font-weight:var(--display-weight)] [letter-spacing:var(--display-tracking)] [text-transform:var(--display-case)]";

/** The creator app's card: soft, rounded and tactile. */
export const panel = "relative rounded-2xl border bg-surface shadow-soft";

function SectionHeading({
  id,
  title,
  count,
  action,
  className,
}: {
  id?: string;
  title: string;
  count?: number;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-3 flex min-h-11 items-center justify-between gap-3", className)}>
      <h2 id={id} className={cn(displayType, "flex items-center gap-2.5 text-[1.375rem] leading-none sm:text-[1.625rem]")}>
        {title}
        {count !== undefined ? (
          <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-surface-3 px-2 font-sans text-xs font-semibold tracking-normal text-muted-foreground normal-case">
            {count}
          </span>
        ) : null}
      </h2>
      {action}
    </div>
  );
}

/** A small neutral pill for facts like platform and claim mode. */
function Chip({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex h-7 items-center gap-1.5 rounded-full border bg-surface-2/70 px-2.5 text-xs font-medium whitespace-nowrap text-foreground/85 [&_svg]:size-3.5 [&_svg]:shrink-0 [&_svg]:text-muted-foreground",
        className,
      )}
    >
      {children}
    </span>
  );
}

/** The NEW marker on fresh drops: the brand signal, used sparingly. */
function NewBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1 rounded-full bg-brand px-2 text-[11px] font-bold tracking-[0.06em] text-brand-foreground uppercase",
        className,
      )}
    >
      <span aria-hidden className="size-1.5 rounded-full bg-current opacity-80" />
      New
    </span>
  );
}

export { Chip, NewBadge, SectionHeading };
