import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileHeroSkeleton() {
  return (
    <div className="px-4 py-8 space-y-6">
      {/* Avatar and username */}
      <div className="flex flex-col items-center gap-3">
        <Skeleton className="w-24 h-24 lg:w-[120px] lg:h-[120px] rounded-full" />
        <div className="text-center space-y-2">
          <Skeleton className="h-8 w-40 mx-auto" />
          <Skeleton className="h-4 w-32 mx-auto" />
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-2xl mx-auto">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="text-center space-y-2">
            <Skeleton className="h-10 w-16 mx-auto" />
            <Skeleton className="h-3 w-20 mx-auto" />
          </div>
        ))}
      </div>

      {/* Audience switch */}
      <div className="flex flex-col items-center gap-2">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-10 w-48 rounded-full" />
      </div>
    </div>
  );
}
