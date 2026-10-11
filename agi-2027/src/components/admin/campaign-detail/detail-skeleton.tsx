import { Skeleton } from "@/components/ui/skeleton";

/** Shown for a moment while a campaign page streams in. */
export function CampaignDetailSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading the campaign">
      <div className="mb-8 flex items-start gap-3.5">
        <Skeleton className="hidden size-14 rounded-[30%] sm:block" />
        <div className="grid flex-1 gap-2">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-8 w-72 max-w-full" />
          <Skeleton className="h-5 w-56" />
        </div>
      </div>
      <Skeleton className="h-28 w-full rounded-lg" />
      <Skeleton className="mt-4 h-96 w-full rounded-lg" />
    </div>
  );
}
