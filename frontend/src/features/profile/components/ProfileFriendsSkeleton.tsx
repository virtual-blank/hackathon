import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileFriendsSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-4">
        <div className="flex items-baseline gap-2">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-5 w-8" />
        </div>
      </div>
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-4 px-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <Skeleton className="w-16 h-16 rounded-full" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
    </div>
  );
}
