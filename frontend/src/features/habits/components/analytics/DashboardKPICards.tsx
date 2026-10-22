import type { DashboardSummarySchema } from "@/api/generated/model";
import { pluralize } from "@/shared/lib/pluralize";
import { Flame, Target, TrendingUp, Users } from "lucide-react";
import { cn } from "@/shared/lib/utils";

type DashboardKPICardsProps = {
  summary: DashboardSummarySchema;
  onClickBestStreak?: () => void;
};

export function DashboardKPICards({ summary, onClickBestStreak }: DashboardKPICardsProps) {
  const bestStreakDaysLabel = pluralize(summary.best_streak_overall, "день", "дня", "дней");
  const totalHabitsLabel = pluralize(summary.total_habits, "привычка", "привычки", "привычек");

  const kpiCards = [
    {
      label: "Лучший стрик",
      value: summary.best_streak_overall,
      unit: bestStreakDaysLabel,
      icon: Flame,
      color: "text-streak",
      onClick: onClickBestStreak,
    },
    {
      label: "Сегодня выполнено",
      value: `${summary.completed_today_count}/${summary.active_habits_count}`,
      unit: "",
      icon: Target,
      color: "text-success",
    },
    {
      label: "Стабильность",
      value: `${Math.round(summary.overall_completion_rate)}%`,
      unit: "",
      icon: TrendingUp,
      color: "text-info",
    },
    {
      label: "Привычки",
      value: summary.total_habits,
      unit: totalHabitsLabel,
      icon: Users,
      color: "text-muted-foreground",
    },
  ];

  return (
    <>
      {kpiCards.map((card) => (
        <button
          key={card.label}
          onClick={card.onClick}
          disabled={!card.onClick}
          className={cn(
            "rounded-[12px] bg-surface border border-border p-4 flex flex-col space-y-3 text-left transition-all",
            card.onClick && "cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
          )}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{card.label}</span>
            <card.icon className={cn("w-5 h-5", card.color)} strokeWidth={1.75} />
          </div>
          <div className="flex items-baseline gap-1">
            <span className="font-display text-2xl font-semibold tabular-nums">
              {card.value}
            </span>
            {card.unit && (
              <span className="text-sm text-muted-foreground">{card.unit}</span>
            )}
          </div>
        </button>
      ))}
    </>
  );
}
