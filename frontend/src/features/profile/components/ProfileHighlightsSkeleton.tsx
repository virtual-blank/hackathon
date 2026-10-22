import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileHighlightsSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-32 ml-4" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 rounded-[16px] bg-surface border border-border space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}
