import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
};

function PageHeader({ eyebrow, title, description, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between lg:mb-10",
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow ? <p className="mb-2.5 text-label text-brand-text">{eyebrow}</p> : null}
        <h1 className="text-h2 text-balance">{title}</h1>
        {description ? (
          <p className="mt-2.5 max-w-2xl text-pretty text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export { PageHeader };
