import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Trash2 } from "lucide-react";
import type { HabitOutputSchema } from "@/api/generated/model";
import { pluralizeDays } from "@/shared/lib/date";
import { ActivityHeatmap } from "@/shared/components/ActivityHeatmap";
import { useHabitLogs } from "../hooks/useHabitLogs";
import { getTodayDate } from "../lib/utils";
import { ErrorState } from "@/shared/components/ErrorState";
import { useMemo } from "react";

type HabitDetailsViewProps = {
  habit: HabitOutputSchema;
  userTimezone: string;
  onEdit: () => void;
  onDelete?: () => void;
};

function getVisibilityLabel(visibility: string): string {
  switch (visibility) {
    case "private":
      return "Приватная";
    case "friends":
      return "Для друзей";
    case "public":
      return "Публичная";
    default:
      return "Неизвестно";
  }
}

export function HabitDetailsView({
  habit,
  userTimezone,
  onEdit,
  onDelete,
}: HabitDetailsViewProps) {
  const today = getTodayDate(userTimezone);
  
  // Calculate start date: 26 weeks ago
  const startDate = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - (26 * 7 - 1));
    return format(date, "yyyy-MM-dd");
  }, []);

  const { data: logs, isLoading, isError, refetch } = useHabitLogs({
    habitId: habit.id,
    startDate: habit.start_date < startDate ? startDate : habit.start_date,
    endDate: today,
  });

  // Build heatmap data
  const heatmapCells = useMemo(() => {
    if (!logs) return [];
    
    const logMap = new Map(logs.map((log) => [log.completed_date, true]));
    const cells = [];
    
    const start = new Date(startDate);
    const end = new Date(today);
    
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const dateStr = format(d, "yyyy-MM-dd");
      const beforeStart = dateStr < habit.start_date;
      cells.push({
        date: dateStr,
        level: (beforeStart ? 0 : logMap.has(dateStr) ? 4 : 0) as 0 | 1 | 2 | 3 | 4,
      });
    }
    
    return cells;
  }, [logs, startDate, today, habit.start_date]);

  const firstLetter = habit.title.charAt(0).toUpperCase();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{
            backgroundColor: `color-mix(in srgb, ${habit.color_hex} 14%, transparent)`,
          }}
        >
          <span className="font-display text-xl font-medium text-foreground">
            {firstLetter}
          </span>
        </div>
        <h2 className="text-2xl font-display font-medium text-foreground flex-1">
          {habit.title}
        </h2>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onEdit}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            aria-label="Редактировать привычку"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-foreground"
            >
              <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" />
              <path d="m15 5 4 4" />
            </svg>
          </button>
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-2 rounded-lg hover:bg-destructive/10 text-destructive transition-colors"
              aria-label="Удалить привычку"
            >
              <Trash2 size={20} strokeWidth={1.75} />
            </button>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Создана</span>
          <span className="text-foreground font-medium">
            {format(new Date(habit.created_at), "d MMMM yyyy", { locale: ru })}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Текущий стрик</span>
          <span className="text-foreground font-medium tabular-nums">
            {habit.current_streak_days} {pluralizeDays(habit.current_streak_days)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Лучший стрик</span>
          <span className="text-foreground font-medium tabular-nums">
            {habit.max_streak_days} {pluralizeDays(habit.max_streak_days)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Видимость</span>
          <span className="text-foreground font-medium">
            {getVisibilityLabel(habit.visibility)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Напоминания</span>
          <span className="text-foreground font-medium">
            {habit.notification_times && habit.notification_times.length > 0
              ? habit.notification_times.map((time) => time.slice(0, 5)).join(", ")
              : "Не заданы"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Выполнено раз</span>
          <span className="text-foreground font-medium tabular-nums">
            {logs?.length ?? 0}
          </span>
        </div>
      </div>

      {/* Heatmap */}
      <div className="space-y-2">
        <h3 className="text-base font-display font-medium text-foreground">
          Карта активности
        </h3>
        {isLoading && (
          <div className="h-32 bg-muted animate-pulse rounded" />
        )}
        {isError && (
          <ErrorState
            message="Не удалось загрузить данные активности"
            onRetry={refetch}
          />
        )}
        {!isLoading && !isError && logs && (
          <ActivityHeatmap cells={heatmapCells} weeksToShow={26} showLegend={false} />
        )}
      </div>
    </div>
  );
}
