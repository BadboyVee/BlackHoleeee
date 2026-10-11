import { cn } from "@/lib/utils";

type PanelProps = {
  /** Used to label the section for screen readers. */
  id?: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
};

/** A flat, hairline-bordered panel: the admin's basic container. */
function Panel({ id, title, description, action, children, className, bodyClassName }: PanelProps) {
  return (
    <section
      aria-labelledby={title && id ? id : undefined}
      className={cn(
        "min-w-0 overflow-hidden rounded-lg border bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)]",
        className,
      )}
    >
      {title ? (
        <div className="flex min-h-13 items-center justify-between gap-3 border-b px-4 py-3 sm:px-5">
          <div className="min-w-0">
            <h2 id={id} className="truncate text-[14px] font-semibold tracking-[-0.01em]">
              {title}
            </h2>
            {description ? <p className="mt-0.5 text-xs text-muted-foreground">{description}</p> : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}

export { Panel };
