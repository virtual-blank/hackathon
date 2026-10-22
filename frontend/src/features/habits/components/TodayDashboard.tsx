import { useMemo, useState } from "react";
import { useGetMeApiV1UsersMeGet } from "@/api/generated/👤-users/👤-users";
import {
  useGetLogsInRangeApiV1HabitsLogsGet,
  getGetLogsInRangeApiV1HabitsLogsGetQueryKey,
} from "@/api/generated/🏃-habits/🏃-habits";
import { useGetDashboardApiV1AnalyticsDashboardGet } from "@/api/generated/📊-analytics/📊-analytics";
import { Flame, Trophy, RotateCcw, ChevronRight, ChevronLeft } from "lucide-react";
import { pluralizeDays } from "@/shared/lib/date";
import { pluralize } from "@/shared/lib/pluralize";
import { Skeleton } from "@/shared/ui/skeleton";
import { Button } from "@/shared/ui/button";
import { ActivityHeatmap } from "@/shared/components/ActivityHeatmap";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/shared/ui/tooltip";
import { addDays, format, subDays } from "date-fns";
import type { HabitOutputSchema, AchievementOutputSchema } from "@/api/generated/model";
import { DashboardExpanded } from "./DashboardExpanded";
import { AchievementDetailsModal } from "./AchievementDetailsModal";
import { resolveAchievementIcon } from "@/shared/lib/achievement-icon";

type TodayDashboardProps = {
  maxStreak: number;
  totalHabitsCount: number;
  bestStreakHabit: HabitOutputSchema | null;
  onOpenBestHabit: () => void;
  completed: HabitOutputSchema[];
  progress: number;
  isDashboardExpanded: boolean;
  onToggleExpanded: () => void;
  onOpenHabit: (habitId: string) => void;
};

export function TodayDashboard({
  maxStreak,
  totalHabitsCount,
  bestStreakHabit,
  onOpenBestHabit,
  completed,
  progress,
  isDashboardExpanded,
  onToggleExpanded,
  onOpenHabit,
}: TodayDashboardProps) {
  const { data: currentUser } = useGetMeApiV1UsersMeGet();
  const [selectedAchievement, setSelectedAchievement] = useState<AchievementOutputSchema | null>(null);

  // Load dashboard data for enriched statistics
  const { data: dashboardData } = useGetDashboardApiV1AnalyticsDashboardGet({ activity_days: 30 });

  const endDate = useMemo(() => new Date(), []);
  const startDate = useMemo(() => addDays(endDate, -98), [endDate]);

  const dateFrom = format(startDate, "yyyy-MM-dd");
  const dateTo = format(endDate, "yyyy-MM-dd");

  const {
    data: logs,
    isLoading: isLogsLoading,
    isError: isLogsError,
    refetch: refetchLogs,
  } = useGetLogsInRangeApiV1HabitsLogsGet(
    {
      date_from: dateFrom,
      date_to: dateTo,
      limit: 1000,
    },
    {
      query: {
        queryKey: getGetLogsInRangeApiV1HabitsLogsGetQueryKey({
          date_from: dateFrom,
          date_to: dateTo,
          limit: 1000,
        }),
      },
    }
  );

  // Compute statistics for summary block
  const uniqueActiveDays = useMemo(() => {
    if (!logs) return 0;
    const thirtyDaysAgo = format(subDays(new Date(), 30), "yyyy-MM-dd");
    const uniqueDates = new Set(
      logs
        .filter((log) => log.completed_date >= thirtyDaysAgo)
        .map((log) => log.completed_date)
    );
    return uniqueDates.size;
  }, [logs]);

  const allHabitsMaxStreak = useMemo(() => {
    if (!bestStreakHabit) return 0;
    // Return the max_streak_days from all habits (already computed as maxStreak in parent)
    return maxStreak;
  }, [bestStreakHabit, maxStreak]);

  const heatmapCells = useMemo(() => {
    if (!logs) return [];

    const dateMap = new Map<string, number>();
    logs.forEach((log) => {
      const count = dateMap.get(log.completed_date) || 0;
      dateMap.set(log.completed_date, count + 1);
    });

    const cells = Array.from(dateMap.entries()).map(([date, completedCount]) => {
      const ratio = completedCount / Math.max(totalHabitsCount, 1);
      let level: 0 | 1 | 2 | 3 | 4;

      if (completedCount === 0) {
        level = 0;
      } else if (ratio <= 0.25) {
        level = 1;
      } else if (ratio <= 0.5) {
        level = 2;
      } else if (ratio <= 0.75) {
        level = 3;
      } else {
        level = 4;
      }

      return { date, level };
    });

    return cells;
  }, [logs, totalHabitsCount]);

  const achievements = useMemo(
    () => currentUser?.achievements || [],
    [currentUser]
  );

  const recentAchievements = useMemo(
    () => achievements.slice(-5).reverse(),
    [achievements]
  );

  // If expanded, show DashboardExpanded
  if (isDashboardExpanded) {
    return (
      <>
        <DashboardExpanded
          onClickBestStreak={onOpenBestHabit}
          onClickHabit={onOpenHabit}
          onClickAchievement={setSelectedAchievement}
          onToggleExpanded={onToggleExpanded}
        />
        {selectedAchievement && (
          <AchievementDetailsModal
            achievement={selectedAchievement}
            open={!!selectedAchievement}
            onOpenChange={(open) => {
              if (!open) setSelectedAchievement(null);
            }}
          />
        )}
      </>
    );
  }

  return (
    <>
    <aside className="relative xl:min-h-0 border-t xl:border-t-0 flex flex-col">
      {/* Background layer with fade at bottom (only on xl+) */}
      <div className="absolute inset-0 bg-surface-muted xl:border-l border-border xl:[mask-image:linear-gradient(to_bottom,black_calc(100%-96px),transparent)]" />
      
      {/* Content layer */}
      <div className="relative p-6 space-y-6 flex-1 pb-24">
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggleExpanded}
                  className="h-7 w-7 shrink-0 inline-flex items-center justify-center rounded-[8px] hover:bg-surface-elevated transition-all"
                  aria-label={isDashboardExpanded ? "Свернуть дашборд" : "Развернуть дашборд"}
                >
                  {isDashboardExpanded ? (
                    <ChevronRight className="w-5 h-5 text-muted-foreground transition-transform" />
                  ) : (
                    <ChevronLeft className="w-5 h-5 text-muted-foreground transition-transform" />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>{isDashboardExpanded ? "Свернуть дашборд" : "Развернуть дашборд"}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <h2 className="font-display text-[24px] font-medium text-foreground">
            Дашборд
          </h2>
        </div>

        <div>
          {dashboardData ? (
            <div className="rounded-[12px] border border-border/70 bg-surface p-4 space-y-3">
              <p className="text-xs text-muted-foreground">Привычки</p>
              
              {/* Total habits count */}
              <div className="flex items-baseline gap-2">
                <span className="font-display text-[32px] font-medium tabular-nums text-foreground">
                  {dashboardData.summary.total_habits}
                </span>
                <span className="text-base text-muted-foreground">
                  {pluralize(dashboardData.summary.total_habits, "привычка", "привычки", "привычек")}
                </span>
              </div>

              {/* Segmented progress bar */}
              <div className="h-2 rounded-full overflow-hidden bg-muted flex">
                <div
                  className="bg-success transition-all"
                  style={{
                    width: `${(dashboardData.summary.active_habits_count / dashboardData.summary.total_habits) * 100}%`,
                  }}
                />
                <div
                  className="bg-destructive/60 transition-all"
                  style={{
                    width: `${(dashboardData.summary.abandoned_habits_count / dashboardData.summary.total_habits) * 100}%`,
                  }}
                />
              </div>

              {/* Detailed summary */}
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Активные:</span>
                  <span className="font-medium text-foreground">{dashboardData.summary.active_habits_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Заброшенные (14+ дн.):</span>
                  <span className="font-medium text-foreground">{dashboardData.summary.abandoned_habits_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Всего выполнений:</span>
                  <span className="font-medium text-foreground">{dashboardData.summary.total_completions_all_time}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Рекордная серия:</span>
                  <span className="font-medium text-foreground">{dashboardData.summary.best_streak_overall} дн.</span>
                </div>
              </div>

              {/* Color dots row */}
              {dashboardData.habits.length > 0 && (
                <div className="flex gap-1.5 mt-3 flex-wrap">
                  {dashboardData.habits.map((habit, idx) => (
                    <div
                      key={`${habit.habit_id}-${idx}`}
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: habit.color_hex }}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : bestStreakHabit ? (
            <button
              onClick={onOpenBestHabit}
              className="w-full text-left rounded-[12px] border border-border/70 bg-surface p-4 transition-all duration-200 group cursor-pointer hover:border-streak/40 hover:shadow-[0_4px_20px_rgba(249,115,22,0.12)] hover:-translate-y-0.5 active:translate-y-0"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Лучший стрик:</p>
                  <div className="flex items-baseline gap-2">
                    <span className="font-display text-[32px] font-medium tabular-nums text-foreground">
                      {maxStreak}
                    </span>
                    <span className="text-base text-muted-foreground">
                      {pluralizeDays(maxStreak)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">серия</p>
                </div>
                <div className="flex items-center gap-2">
                  <Flame
                    size={40}
                    strokeWidth={1.5}
                    className="text-muted-foreground transition-all duration-200 group-hover:scale-110 group-hover:text-streak"
                  />
                  <ChevronRight
                    size={20}
                    strokeWidth={1.75}
                    className="text-muted-foreground/40 transition-transform duration-200 group-hover:translate-x-1"
                  />
                </div>
              </div>
            </button>
          ) : (
            <div className="rounded-[12px] border border-border/70 bg-surface p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Лучший стрик:</p>
                  <div className="flex items-baseline gap-2">
                    <span className="font-display text-[32px] font-medium tabular-nums text-foreground">
                      0
                    </span>
                    <span className="text-base text-muted-foreground">
                      дней
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">серия</p>
                </div>
                <Flame
                  size={40}
                  strokeWidth={1.5}
                  className="text-muted-foreground"
                />
              </div>
            </div>
          )}
        </div>

        <div>
          <h3 className="font-display text-[18px] font-medium text-foreground mb-3">
            Карта активности
          </h3>
          {isLogsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-[120px] w-full rounded-[12px]" />
              <div className="flex items-center gap-1">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-3 rounded-[2px]" />
                <Skeleton className="h-3 w-3 rounded-[2px]" />
                <Skeleton className="h-3 w-3 rounded-[2px]" />
                <Skeleton className="h-3 w-3 rounded-[2px]" />
                <Skeleton className="h-3 w-3 rounded-[2px]" />
              </div>
            </div>
          ) : isLogsError ? (
            <div className="rounded-[12px] border border-border bg-surface p-4 text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Не удалось загрузить данные активности
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => refetchLogs()}
                className="gap-2"
              >
                <RotateCcw size={14} />
                Повторить
              </Button>
            </div>
          ) : (
            <ActivityHeatmap cells={heatmapCells} weeksToShow={13} />
          )}
        </div>

        <div>
          <h3 className="font-display text-[18px] font-medium text-foreground mb-3">
            Достижения
          </h3>
          {achievements.length === 0 ? (
            <div className="rounded-[12px] border border-border bg-surface p-4 text-center space-y-2">
              <Trophy
                size={32}
                strokeWidth={1.5}
                className="mx-auto text-muted-foreground opacity-40"
                aria-hidden="true"
              />
              <p className="text-sm text-muted-foreground">
                Выполняйте привычки, чтобы открыть первые достижения
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <TooltipProvider>
                <div className="grid grid-cols-3 gap-3">
                  {recentAchievements.map((achievement, idx) => {
                    const iconSrc = resolveAchievementIcon(achievement.icon_url);
                    return (
                      <Tooltip key={`${achievement.name}-${idx}`}>
                        <TooltipTrigger asChild>
                          <button
                            onClick={() => setSelectedAchievement(achievement)}
                            className="group relative flex flex-col items-center transition-transform hover:scale-110 hover:-translate-y-1 shrink-0"
                          >
                            {/* Glow layer */}
                            <div
                              className="absolute inset-0 rounded-full blur-[24px] opacity-20 group-hover:opacity-35 group-hover:blur-[32px] transition-all pointer-events-none"
                              style={{
                                background: `radial-gradient(circle, ${achievement.color_hex}, transparent 70%)`,
                              }}
                            />
                            
                            {/* Icon */}
                            <img
                              src={iconSrc}
                              alt={achievement.name}
                              className="relative z-10 w-16 h-16 shrink-0 aspect-square object-contain drop-shadow-lg transition-transform"
                              onError={(e) => {
                                e.currentTarget.src = '/default-achievement.png';
                              }}
                            />
                            
                            {/* Name below */}
                            <p className="relative z-10 text-xs font-medium text-foreground text-center mt-2 max-w-[80px] truncate">
                              {achievement.name}
                            </p>
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            <p className="font-medium">{achievement.name}</p>
                            <p className="text-xs text-primary-foreground/80">
                              {achievement.description}
                            </p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              </TooltipProvider>
              {achievements.length > 5 && (
                <button
                  onClick={onToggleExpanded}
                  className="text-xs text-muted-foreground hover:text-foreground text-right transition-colors underline decoration-dashed underline-offset-2"
                >
                  +{achievements.length - 5} ещё
                </button>
              )}
            </div>
          )}
        </div>

        {/* Summary Statistics */}
        <div>
          <p className="text-sm text-muted-foreground mb-3">Сводка</p>
          <div className="grid grid-cols-2 gap-2.5">
            {/* Plan for today */}
            <div className="rounded-[12px] bg-surface border border-border/70 p-3">
              <p className="font-display text-xl tabular-nums text-foreground mb-1">
                {progress}%
              </p>
              <p className="text-xs text-muted-foreground leading-tight">
                {completed.length} из {totalHabitsCount} выполнено
              </p>
            </div>
            
            {/* Total completions */}
            <div className="rounded-[12px] bg-surface border border-border/70 p-3">
              <p className="font-display text-xl tabular-nums text-foreground mb-1">
                {logs?.length ?? 0}
              </p>
              <p className="text-xs text-muted-foreground leading-tight">
                за 3 месяца
              </p>
            </div>
            
            {/* Active days in last 30 days */}
            <div className="rounded-[12px] bg-surface border border-border/70 p-3">
              <p className="font-display text-xl tabular-nums text-foreground mb-1">
                {uniqueActiveDays}
              </p>
              <p className="text-xs text-muted-foreground leading-tight">
                за 30 дней
              </p>
            </div>
            
            {/* Record streak */}
            <div className="rounded-[12px] bg-surface border border-border/70 p-3">
              <p className="font-display text-xl tabular-nums text-foreground mb-1">
                {allHabitsMaxStreak}
              </p>
              <p className="text-xs text-muted-foreground leading-tight">
                лучший результат
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
    {selectedAchievement && (
      <AchievementDetailsModal
        achievement={selectedAchievement}
        open={!!selectedAchievement}
        onOpenChange={(open) => {
          if (!open) setSelectedAchievement(null);
        }}
      />
    )}
    </>
  );
}

