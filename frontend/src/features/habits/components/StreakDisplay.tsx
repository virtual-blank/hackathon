import { Flame } from "lucide-react";
import { cn } from "@/shared/lib/utils";

type StreakDisplayProps = {
  streak: number;
  className?: string;
  size?: "sm" | "md" | "lg";
};

const sizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-2xl",
};

const iconSizes = {
  sm: 16,
  md: 20,
  lg: 28,
};

export function StreakDisplay({
  streak,
  className,
  size = "md",
}: StreakDisplayProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-streak font-semibold tabular-nums",
        sizeClasses[size],
        className
      )}
    >
      <Flame size={iconSizes[size]} className="fill-streak" />
      <span>{streak}</span>
    </div>
  );
}
