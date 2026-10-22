import { cn } from "@/shared/lib/utils";

type DailyProgressRingProps = {
  progress: number; // 0-100
  completed: number;
  total: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
};

export function DailyProgressRing({
  progress,
  completed,
  total,
  size = 140,
  strokeWidth = 12,
  className,
}: DailyProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className={cn("relative inline-flex", className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--primary)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums text-foreground">
          {completed}
        </span>
        <span className="text-sm text-muted-foreground">/ {total}</span>
      </div>
    </div>
  );
}
