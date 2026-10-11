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
        "flex flex-col items-center rounded-2xl border bg-surface/50 px-6 py-14 text-center sm:py-20",
        className,
      )}
    >
      <div className="mb-5 flex size-10 items-center justify-center rounded-xl border bg-surface-2">
        <Icon className="size-[18px] text-muted-foreground" />
      </div>
      <h3 className="text-[15px] font-semibold tracking-[-0.015em]">{title}</h3>
      <div className="mt-1.5 max-w-sm text-sm text-pretty text-muted-foreground">{description}</div>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

export { EmptyState };
