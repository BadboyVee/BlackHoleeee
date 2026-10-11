import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: React.ReactNode;
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
        {eyebrow ? <div className="mb-2 text-sm font-medium text-muted-foreground">{eyebrow}</div> : null}
        <h1 className="text-[1.75rem] leading-tight font-semibold tracking-[-0.035em] text-balance sm:text-[2rem]">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-2xl text-[15px] text-pretty text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export { PageHeader };
