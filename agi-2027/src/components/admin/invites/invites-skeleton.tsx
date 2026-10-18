import { Skeleton } from "@/components/ui/skeleton";

import { INVITES_GRID } from "./layout";

/** Shown for a moment while the invite links stream in. Same shape as the page, so nothing jumps. */
export function InvitesSkeleton() {
  return (
    <div role="status" className={INVITES_GRID}>
      <span className="sr-only">Loading invite links</span>
      <div className="rounded-lg border bg-surface">
        <div className="border-b px-4 py-4 sm:px-5">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="mt-2 h-3 w-56 max-w-full" />
        </div>
        <div className="grid gap-5 p-4 sm:p-5">
          <Skeleton className="h-11 w-full rounded-xl" />
          <Skeleton className="h-11 w-full rounded-xl sm:w-48" />
          <div className="flex flex-wrap gap-2">
            {["w-20", "w-24", "w-26", "w-28", "w-28"].map((width, index) => (
              <Skeleton key={index} className={`h-11 rounded-full ${width}`} />
            ))}
          </div>
          <Skeleton className="h-11 w-full rounded-full" />
        </div>
      </div>
      <div className="rounded-lg border bg-surface">
        <div className="border-b px-4 py-4 sm:px-5">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="mt-2 h-3 w-40 max-w-full" />
        </div>
        {[0, 1, 2].map((row) => (
          <div key={row} className="grid gap-3 border-b px-4 py-4 last:border-b-0 sm:px-5">
            <div className="flex items-center justify-between gap-3">
              <Skeleton className="h-4 w-44 max-w-full" />
              <Skeleton className="h-5.5 w-16 shrink-0 rounded-full" />
            </div>
            <Skeleton className="h-11 w-full rounded-xl" />
            <Skeleton className="h-4 w-64 max-w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
