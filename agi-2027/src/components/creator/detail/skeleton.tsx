import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { panel } from "../ui";

/** The campaign page's shape while it loads, so nothing jumps when it arrives. */
export function DetailSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading campaign" className="flex flex-col gap-6 pt-1 sm:pt-3">
      <div className={cn(panel, "flex flex-col gap-5 p-5 sm:p-7")}>
        <div className="flex items-center gap-3.5">
          <Skeleton className="size-14 rounded-2xl" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3.5 w-48" />
          </div>
        </div>
        <Skeleton className="h-10 w-4/5" />
        <Skeleton className="h-5 w-full max-w-xl" />
        <div className="flex gap-2">
          <Skeleton className="h-7 w-28 rounded-full" />
          <Skeleton className="h-7 w-28 rounded-full" />
        </div>
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
          <Skeleton className="col-span-2 h-24 rounded-xl sm:col-span-1" />
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20.5rem] lg:gap-8">
        <div className="flex flex-col gap-5">
          {[0, 1].map((key) => (
            <div key={key} className={cn(panel, "flex flex-col gap-3 p-5 sm:p-6")}>
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          ))}
        </div>
        <Skeleton className="hidden h-72 rounded-2xl lg:block" />
      </div>
    </div>
  );
}
