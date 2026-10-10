import * as React from "react";

import { cn } from "@/lib/utils";

type EmptyStateProps = {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  /** Tell people what happens next or what to do. */
  description: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
};

function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      data-slot="empty-state"
      className={cn(
        "relative flex flex-col items-center overflow-hidden rounded-2xl border border-dashed border-border-strong px-6 py-12 text-center sm:py-16",
        className,
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 left-1/2 h-48 w-72 -translate-x-1/2 rounded-full bg-(--glow) blur-3xl"
      />
      <div className="relative mb-5 flex size-14 items-center justify-center rounded-2xl border border-border-strong bg-surface shadow-[inset_0_1px_0_0_var(--card-highlight)]">
        <Icon className="size-6 text-brand-text" />
      </div>
      <h3 className="relative text-base font-semibold tracking-tight">{title}</h3>
      <p className="relative mt-1.5 max-w-sm text-sm text-pretty text-muted-foreground">
        {description}
      </p>
      {action ? <div className="relative mt-6">{action}</div> : null}
    </div>
  );
}

export { EmptyState };
