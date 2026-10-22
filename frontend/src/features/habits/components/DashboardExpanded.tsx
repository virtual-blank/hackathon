import { useState } from "react";
import { useGetMeApiV1UsersMeGet } from "@/api/generated/👤-users/👤-users";
import {
  useGetDashboardApiV1AnalyticsDashboardGet,
} from "@/api/generated/📊-analytics/📊-analytics";
import type { AchievementOutputSchema } from "@/api/generated/model";
import { DashboardKPICards } from "./analytics/DashboardKPICards";
import { DailyActivityChart } from "./analytics/DailyActivityChart";
import { WeekdayActivityChart } from "./analytics/WeekdayActivityChart";
import { HabitsRankingList } from "./analytics/HabitsRankingList";
import { ActivityHeatmap } from "@/shared/components/ActivityHeatmap";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/components/ErrorState";
import { EmptyState } from "@/shared/components/EmptyState";
import { BarChart3, Trophy, Calendar, TrendingUp, AlertCircle, ChevronRight, ArrowUp, ArrowDown } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { pluralize } from "@/shared/lib/pluralize";
import { resolveAchievementIcon } from "@/shared/lib/achievement-icon";

type DashboardExpandedProps = {
  onClickBestStreak?: () => void;
  onClickHabit: (habitId: string) => void;
  onClickAchievement: (achievement: AchievementOutputSchema) => void;
  onToggleExpanded: () => void;
};

export function DashboardExpanded({
  onClickBestStreak,
  onClickHabit,
  onClickAchievement,
  onToggleExpanded,
}: DashboardExpandedProps) {
  const [activityDays, setActivityDays] = useState(30);
  const { data: currentUser } = useGetMeApiV1UsersMeGet();
  
  const {
    data: dashboardData,
    isLoading,
    isError,
    refetch,
  } = useGetDashboardApiV1AnalyticsDashboardGet({ activity_days: activityDays });

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6 p-6 bg-surface-muted rounded-[16px] border border-border overflow-y-auto h-full">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-9 w-48" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-[12px]" />
          ))}
          <Skeleton className="col-span-1 md:col-span-2 h-64 rounded-[16px]" />
          <Skeleton className="col-span-1 h-64 rounded-[16px]" />
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !dashboardData) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <ErrorState
          title="Не удалось загрузить аналитику"
          message="Проверьте интернет-соединение и попробуйте ещё раз"
          onRetry={refetch}
        />
      </div>
    );
  }

  // Empty state
  if (dashboardData.habits.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <EmptyState
          title="Нет данных для аналитики"
          description="Начните отмечать привычки, чтобы увидеть статистику"
          illustration={
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <BarChart3 className="w-8 h-8 text-muted-foreground" />
            </div>
          }
        />
      </div>
    );
  }

  // Transform daily_activity into heatmap cells
  const heatmapCells = dashboardData.daily_activity.map((point) => {
    const count = point.completed_count;
    let level: 0 | 1 | 2 | 3 | 4 = 0;
    if (count >= 8) level = 4;
    else if (count >= 6) level = 3;
    else if (count >= 4) level = 2;
    else if (count >= 1) level = 1;

    return {
      date: point.date,
      level,
    };
  });

  return (
    <div className="space-y-6 p-6 bg-surface-muted rounded-[16px] border border-border overflow-y-auto h-full">
      {/* Header with collapse button and period selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleExpanded}
            className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Свернуть дашборд"
          >
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          </button>
          <h3 className="font-display text-2xl font-medium text-foreground">Дашборд</h3>
        </div>
        
        <div className="inline-flex rounded-[10px] bg-surface border border-border p-1">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setActivityDays(days)}
              className={cn(
                "px-3 py-1.5 text-sm font-medium rounded-[8px] transition-all",
                activityDays === days 
                  ? "bg-surface-elevated shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {days} дн.
            </button>
          ))}
        </div>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-4">
        {/* KPI Cards */}
        <DashboardKPICards 
          summary={dashboardData.summary} 
          onClickBestStreak={onClickBestStreak}
        />

        {/* Daily Activity Chart */}
        <DailyActivityChart data={dashboardData.daily_activity} />

        {/* Weekday Activity Chart */}
        <WeekdayActivityChart data={dashboardData.weekday_activity} />

        {/* Pulse & Insights */}
        <div className="col-span-1 rounded-[16px] bg-surface border border-border p-4 space-y-4">
          <h4 className="font-display text-base font-medium">Пульс и инсайты</h4>
          
          {/* Most productive day */}
          {dashboardData.weekday_activity.length > 0 && (() => {
            const mostProductiveDay = dashboardData.weekday_activity.reduce((max, day) =>
              day.completed_count > max.completed_count ? day : max
            );
            return (
              <div className="flex items-start gap-3 p-3 rounded-[12px] bg-surface-muted">
                <Calendar className="w-5 h-5 text-info shrink-0 mt-0.5" strokeWidth={1.75} />
                <div className="space-y-1">
                  <p className="text-sm font-medium">Пик активности</p>
                  <p className="text-xs text-muted-foreground">
                    {mostProductiveDay.weekday_name} ({mostProductiveDay.completed_count} {pluralize(mostProductiveDay.completed_count, "выполнение", "выполнения", "выполнений")})
                  </p>
                </div>
              </div>
            );
          })()}
          
          {/* Social support */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Социальный отклик</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-[8px] bg-success/10 border border-success/20">
                <p className="text-lg font-display font-semibold tabular-nums text-success">
                  {dashboardData.summary.total_pushes_received}
                </p>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <ArrowUp className="w-3.5 h-3.5 text-success shrink-0" strokeWidth={2}/>
                  <span>Пушей</span>
                </p>
              </div>
              <div className="p-2.5 rounded-[8px] bg-destructive/10 border border-destructive/20">
                <p className="text-lg font-display font-semibold tabular-nums text-destructive">
                  {dashboardData.summary.total_shames_received}
                </p>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <ArrowDown className="w-3.5 h-3.5 text-destructive shrink-0" strokeWidth={2}/>
                  <span>Шеймов</span>
                </p>
              </div>
            </div>
          </div>
          
          {/* Focus attention */}
          {dashboardData.abandoned_habits.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-destructive" strokeWidth={1.75} />
                Требуют внимания
              </p>
              <div className="space-y-1.5">
                {dashboardData.abandoned_habits.slice(0, 2).map((habit) => (
                  <button
                    key={habit.habit_id}
                    onClick={() => onClickHabit(habit.habit_id)}
                    className="w-full flex items-center justify-between p-2.5 rounded-[8px] bg-surface-muted hover:bg-muted transition-colors text-left"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: habit.color_hex }}
                      />
                      <span className="text-xs font-medium truncate">{habit.title}</span>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0 ml-2">
                      {habit.days_since_last_log} дн.
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-[12px] bg-success/5 border border-success/15">
              <div className="flex items-start gap-2.5">
                <TrendingUp className="w-5 h-5 text-success shrink-0 mt-0.5" strokeWidth={1.75} />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-success">Все привычки в отличном темпе!</p>
                  {(() => {
                    const bestHabit = dashboardData.habits.reduce((max, h) =>
                      h.completion_rate > max.completion_rate ? h : max
                    );
                    return (
                      <p className="text-xs text-muted-foreground">
                        Лучшая: {bestHabit.title} ({Math.round(bestHabit.completion_rate)}%)
                      </p>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Habits Ranking */}
        <HabitsRankingList 
          habits={dashboardData.habits} 
          onClickHabit={onClickHabit}
        />

        {/* Activity Heatmap */}
        <div className="col-span-1 md:col-span-2 2xl:col-span-3 rounded-[16px] bg-surface border border-border p-4 space-y-3">
          <h4 className="font-display text-base font-medium">Карта активности</h4>
          <ActivityHeatmap 
            cells={heatmapCells}
            weeksToShow={26}
          />
        </div>

        {/* Achievements */}
        {currentUser?.achievements && currentUser.achievements.length > 0 && (
          <div className="col-span-1 md:col-span-2 2xl:col-span-3 rounded-[16px] bg-surface border border-border p-4 space-y-3">
            <h4 className="font-display text-base font-medium flex items-center gap-2">
              <Trophy className="w-5 h-5 text-streak" />
              Достижения
            </h4>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
              {currentUser.achievements.map((achievement, idx) => {
                const iconSrc = resolveAchievementIcon(achievement.icon_url);
                return (
                  <button
                    key={`${achievement.name}-${idx}`}
                    onClick={() => onClickAchievement(achievement)}
                    className="group relative flex flex-col items-center transition-transform hover:scale-110 hover:-translate-y-1"
                  >
                    {/* Glow layer */}
                    <div
                      className="absolute inset-0 rounded-full blur-[20px] opacity-18 group-hover:opacity-32 group-hover:blur-[24px] scale-110 transition-all pointer-events-none"
                      style={{
                        background: `radial-gradient(circle, ${achievement.color_hex} 20%, transparent 65%)`,
                      }}
                    />
                    
                    {/* Icon */}
                    <img
                      src={iconSrc}
                      alt={achievement.name}
                      className="relative z-10 w-20 h-20 shrink-0 aspect-square object-contain drop-shadow-lg transition-transform"
                      onError={(e) => {
                        e.currentTarget.src = "/default-achievement.png";
                      }}
                    />
                    
                    {/* Name below */}
                    <p className="relative z-10 text-sm font-medium text-foreground text-center mt-3 max-w-[100px]">
                      {achievement.name}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
