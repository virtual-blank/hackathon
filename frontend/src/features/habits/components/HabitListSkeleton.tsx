import { Skeleton } from "@/shared/ui/skeleton";

export function HabitListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="w-full min-h-[72px] rounded-2xl border border-border bg-card p-4 flex items-center gap-4"
        >
          <Skeleton className="w-1 h-12 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="w-11 h-11 rounded-full" />
        </div>
      ))}
    </div>
  );
}
