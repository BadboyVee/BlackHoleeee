import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { panel } from "../ui";

function PanelSkeleton({ rows }: { rows: number }) {
  return (
    <div>
      <Skeleton className="mb-2.5 h-7 w-48 rounded-lg" />
      <Skeleton className="mb-4 h-4 w-64 max-w-full" />
      <div className={cn(panel, "grid gap-5 p-4 sm:p-6")}>
        {Array.from({ length: rows }, (_, index) => (
          <div key={index} className="grid gap-2">
            <Skeleton className="h-3.5 w-28" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** The profile page's shape while it loads: photo, then three panels of fields. */
export function ProfileSkeleton() {
  return (
    <div className="flex flex-col gap-10">
      <p role="status" className="sr-only">
        Loading your profile
      </p>
      <div>
        <Skeleton className="mb-2.5 h-7 w-56 rounded-lg" />
        <Skeleton className="mb-4 h-4 w-72 max-w-full" />
        <div className={cn(panel, "grid gap-6 p-4 sm:p-6")}>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:gap-6">
            <Skeleton className="size-24 shrink-0 rounded-full sm:size-28" />
            <div className="grid w-full max-w-xs justify-items-center gap-3 sm:justify-items-start">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-11 w-36 rounded-full" />
            </div>
          </div>
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="grid gap-2">
              <Skeleton className="h-3.5 w-28" />
              <Skeleton className="h-11 w-full rounded-xl" />
            </div>
          ))}
        </div>
      </div>
      <PanelSkeleton rows={3} />
      <PanelSkeleton rows={1} />
    </div>
  );
}
