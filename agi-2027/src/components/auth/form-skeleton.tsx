import { Skeleton } from "@/components/ui/skeleton";

/** What a sign-in page shows for the moment before its form streams in. */
export function AuthFormSkeleton({ fields = 2, title }: { fields?: number; title: string }) {
  return (
    <div className="grid gap-6" aria-busy>
      <div className="grid justify-items-center gap-3">
        <Skeleton className="h-3 w-24" />
        <h1 className="text-h2">{title}</h1>
        <Skeleton className="h-4 w-64 max-w-full" />
      </div>
      <div className="grid gap-5">
        {Array.from({ length: fields }, (_, index) => (
          <div key={index} className="grid gap-2">
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        ))}
        <Skeleton className="h-12 w-full rounded-full" />
      </div>
    </div>
  );
}
