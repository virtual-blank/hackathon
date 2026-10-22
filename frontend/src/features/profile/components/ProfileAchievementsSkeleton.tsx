import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileAchievementsSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-5 w-8" />
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4 px-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="aspect-square rounded-[12px]" />
        ))}
      </div>
    </div>
  );
}
