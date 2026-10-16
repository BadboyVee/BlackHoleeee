import { Skeleton } from "@/components/ui/skeleton";

/** Shown for a moment while the applications stream in. */
export function ApplicationsSkeleton() {
  return (
    <div role="status" className="grid max-w-5xl grid-cols-1 gap-4">
      <span className="sr-only">Loading applications</span>
      <div className="flex h-11 items-center gap-3 border-b">
        {["w-20", "w-24", "w-22", "w-12"].map((width) => (
          <Skeleton key={width} className={`h-5 rounded-full ${width}`} />
        ))}
      </div>
      <Skeleton className="h-4 w-52 max-w-full" />
      {[0, 1].map((card) => (
        <div key={card} className="rounded-lg border bg-surface p-4 sm:p-5">
          <div className="flex items-start gap-3">
            <Skeleton className="size-10 shrink-0 rounded-full" />
            <div className="grid flex-1 gap-2">
              <Skeleton className="h-4 w-40 max-w-full" />
              <Skeleton className="h-3.5 w-64 max-w-full" />
            </div>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-2.5">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
          <Skeleton className="mt-5 h-20 w-full" />
        </div>
      ))}
    </div>
  );
}
