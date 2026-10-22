import { Skeleton } from "@/shared/ui/skeleton";

export function ProfileActivitySkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48 ml-4" />
      <div className="px-4">
        <Skeleton className="h-32 w-full max-w-3xl mx-auto" />
      </div>
    </div>
  );
}
