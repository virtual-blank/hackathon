import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileHabitsShowcaseSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-4">
        <Skeleton className="h-8 w-48" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 px-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-24 rounded-[12px]" />
        ))}
      </div>
    </div>
  );
}
