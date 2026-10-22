import { Skeleton } from '@/shared/ui/skeleton'

export function FeedSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="rounded-[20px] border border-border bg-surface p-5 md:p-6 space-y-5"
        >
          {/* Header */}
          <div className="flex items-center gap-3">
            <Skeleton className="w-11 h-11 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-6 w-20" />
          </div>

          {/* Title */}
          <div className="flex items-center gap-3">
            <Skeleton className="w-1.5 h-7 rounded-full" />
            <Skeleton className="h-6 w-48" />
          </div>

          {/* Heatmap area */}
          <div className="rounded-[14px] bg-surface-muted/70 border border-border/60 p-3.5 space-y-3">
            <Skeleton className="h-4 w-32" />
            <div className="grid grid-cols-16 gap-1">
              {Array.from({ length: 16 * 7 }).map((_, j) => (
                <Skeleton key={j} className="w-3 h-3 rounded-[3px]" />
              ))}
            </div>
          </div>

          {/* Reaction bar */}
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-24 rounded-full" />
            <Skeleton className="h-10 w-24 rounded-full" />
            <Skeleton className="h-10 w-28 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  )
}
