import { useState, useMemo, Fragment, useEffect } from "react";
import { useGetMeApiV1UsersMeGet } from "@/api/generated/👤-users/👤-users";
import { useTodayHabits } from "../hooks/useTodayHabits";
import { useToggleHabit } from "../hooks/useToggleHabit";
import { getTodayDate, getMaxStreak } from "../lib/utils";
import { getBestStreakHabit } from "../lib/streak-best";
import { formatFullDate } from "@/shared/lib/date";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { HabitListSkeleton } from "../components/HabitListSkeleton";
import { HabitCard } from "../components/HabitCard";
import { TodayFilters } from "../components/TodayFilters";
import { HabitDetailsModal } from "../components/HabitDetailsModal";
import { TodayDashboard } from "../components/TodayDashboard";
import { Progress } from "@/shared/ui/progress";
import { Button } from "@/shared/ui/button";
import { useAppShellStore } from "@/shared/lib/app-shell-store";
import { Plus, Sparkles, RotateCcw, CircleCheck } from "lucide-react";
import { motion, LayoutGroup } from "motion/react";
import { addDays, differenceInDays } from "date-fns";


type FilterStatus = "all" | "completed" | "uncompleted";

export function TodayPage() {
  const { data: currentUser, isLoading: isUserLoading } =
    useGetMeApiV1UsersMeGet();
  const { setCreateHabitSheetOpen } = useAppShellStore();

  const todayDate = currentUser?.timezone
    ? getTodayDate(currentUser.timezone)
    : getTodayDate("UTC");

  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  // Store selected date as offset from today (null = today)
  const [selectedDateOffset, setSelectedDateOffset] = useState<number | null>(null);
  const [selectedHabitId, setSelectedHabitId] = useState<string | null>(null);
  const [openBestStreak, setOpenBestStreak] = useState(false);
  const [dayCounter, setDayCounter] = useState(0); // Force re-render on day change
  const [isDashboardExpanded, setIsDashboardExpanded] = useState(false);

  // Compute selectedDate from offset
  const selectedDate = selectedDateOffset === null ? todayDate : addDays(new Date(todayDate), selectedDateOffset).toISOString().split('T')[0];

  // Timer to refresh todayDate at midnight in user's timezone
  useEffect(() => {
    if (!currentUser?.timezone) return;

    const scheduleNextMidnight = () => {
      try {
        const now = new Date();
        const formatter = new Intl.DateTimeFormat("en-CA", {
          timeZone: currentUser.timezone,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        });
        const parts = formatter.formatToParts(now);
        const tzNow = new Date(
          `${parts.find(p => p.type === "year")?.value}-${parts.find(p => p.type === "month")?.value}-${parts.find(p => p.type === "day")?.value}T${parts.find(p => p.type === "hour")?.value}:${parts.find(p => p.type === "minute")?.value}:${parts.find(p => p.type === "second")?.value}`
        );
        
        const midnight = new Date(tzNow);
        midnight.setHours(24, 0, 0, 0);
        const msUntilMidnight = midnight.getTime() - tzNow.getTime();

        const timer = setTimeout(() => {
          setDayCounter(prev => prev + 1);
          scheduleNextMidnight();
        }, msUntilMidnight);

        return () => clearTimeout(timer);
      } catch {
        // Fallback: check every minute
        const timer = setInterval(() => {
          setDayCounter(prev => prev + 1);
        }, 60000);
        return () => clearInterval(timer);
      }
    };

    const cleanup = scheduleNextMidnight();
    return cleanup;
  }, [currentUser?.timezone, dayCounter]);

  const {
    completed,
    uncompleted,
    all,
    progress,
    isLoading: isHabitsLoading,
    isError,
    refetch,
  } = useTodayHabits(selectedDate);

  const toggleHabit = useToggleHabit({ date: selectedDate });

  const isLoading = isUserLoading || isHabitsLoading;
  const isToday = selectedDate === todayDate;

  const maxStreak = useMemo(() => getMaxStreak(all), [all]);

  // Find habit with best streak using deterministic tie-breaker
  const bestStreakHabit = useMemo(() => getBestStreakHabit(all), [all]);

  // Filter habits by status
  const filteredHabits = useMemo(() => {
    const uncompletedList =
      filterStatus === "completed" ? [] : uncompleted;
    const completedList = filterStatus === "uncompleted" ? [] : completed;

    return {
      uncompleted: uncompletedList,
      completed: completedList,
      all:
        filterStatus === "all"
          ? all
          : filterStatus === "completed"
            ? completed
            : uncompleted,
    };
  }, [filterStatus, completed, uncompleted, all]);

  const isFiltered = filterStatus !== "all" || selectedDate !== todayDate;
  const allCompleted = all.length > 0 && completed.length === all.length;

  // Find selected habit
  const selectedHabit = selectedHabitId
    ? all.find((h) => h.id === selectedHabitId)
    : null;

  // Close modal if habit not found
  if (selectedHabitId && !selectedHabit) {
    setSelectedHabitId(null);
  }

  // Greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Доброе утро";
    if (hour < 18) return "Добрый день";
    return "Добрый вечер";
  };

  const handleResetFilter = () => {
    setFilterStatus("all");
    setSelectedDateOffset(null);
  };

  // Error state
  if (isError && !isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ErrorState
          message="Не удалось загрузить привычки"
          onRetry={refetch}
        />
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div className="space-y-2">
          <div className="h-10 w-80 bg-muted animate-pulse rounded" />
          <div className="h-5 w-56 bg-muted animate-pulse rounded" />
        </div>
        <div className="space-y-3">
          <div className="h-6 w-48 bg-muted animate-pulse rounded" />
          <div className="h-1 w-full bg-muted animate-pulse rounded" />
        </div>
        <HabitListSkeleton count={3} />
      </div>
    );
  }

  // Empty state: no habits at all
  if (all.length === 0 && !isFiltered) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8 space-y-1">
          <h1 className="text-[32px] leading-tight font-display font-medium text-foreground">
            {getGreeting()}
            {currentUser?.username ? `, ${currentUser.username}` : ""}!
          </h1>
          <p className="text-[14px] text-muted-foreground">
            {formatFullDate(new Date(), currentUser?.timezone)}
          </p>
        </div>
        <EmptyState
          title="Начните отслеживать привычки"
          description="Создайте свою первую привычку и начните строить новый образ жизни"
          illustration={
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-10 h-10 text-primary" />
            </div>
          }
        />
        <div className="flex justify-center mt-6">
          <Button
            onClick={() => setCreateHabitSheetOpen(true)}
            size="lg"
            className="gap-2"
          >
            <Plus size={20} />
            Создать привычку
          </Button>
        </div>
      </div>
    );
  }

  // Success state
  return (
    <Fragment>
      <div 
        className="min-h-0 flex-1 grid gap-0 transition-[grid-template-columns] duration-300 ease-out"
        style={{
          gridTemplateColumns: isDashboardExpanded 
            ? 'minmax(0, 380px) 1fr' 
            : '1fr minmax(0, 340px)'
        }}
      >
        {/* Left column: habits list */}
        <div className="max-w-5xl mx-auto px-4 py-8 space-y-8 overflow-y-auto min-h-0 w-full">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-[32px] leading-tight font-display font-medium text-foreground">
          {getGreeting()}
          {currentUser?.username ? `, ${currentUser.username}` : ""}!
        </h1>
        <p className="text-[14px] text-muted-foreground">
          {formatFullDate(selectedDate, currentUser?.timezone)}
        </p>
      </div>

      {/* Habits List */}
      <div className="space-y-4">
        <div className="space-y-3">
          {/* Section header with counter and filter */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-[20px] font-display font-medium text-foreground">
                Сегодняшние привычки
              </h2>
              <span className="text-[15px] text-muted-foreground shrink-0 whitespace-nowrap tabular-nums">
                {completed.length}/{all.length}
              </span>
              {allCompleted && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 500, damping: 25 }}
                  className="motion-reduce:transition-none motion-reduce:animate-none"
                >
                  <CircleCheck
                    className="text-success"
                    size={20}
                    aria-label="Все привычки выполнены"
                  />
                </motion.div>
              )}
            </div>
            <TodayFilters
              status={filterStatus}
              date={selectedDate}
              onStatusChange={setFilterStatus}
              onDateChange={(newDate) => {
                const offset = newDate === todayDate ? null : differenceInDays(new Date(newDate), new Date(todayDate));
                setSelectedDateOffset(offset);
              }}
            />
          </div>

          {/* Progress bar */}
          <Progress value={progress} className="h-1" />
        </div>

        {/* Empty filter result */}
        {filteredHabits.all.length === 0 ? (
          <div className="py-12">
            <EmptyState
              title="Нет привычек по выбранному фильтру"
              description="Попробуйте изменить параметры фильтрации"
              illustration={
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                  <RotateCcw className="w-8 h-8 text-muted-foreground" />
                </div>
              }
            />
            <div className="flex justify-center mt-6">
              <Button
                onClick={handleResetFilter}
                variant="outline"
                size="default"
                className="gap-2"
              >
                <RotateCcw size={16} />
                Сбросить фильтр
              </Button>
            </div>
          </div>
        ) : (
          <LayoutGroup>
            <div className="space-y-3 habit-list">
              {/* Uncompleted first */}
              {filteredHabits.uncompleted.map((habit) => (
                <HabitCard
                  key={habit.id}
                  habit={habit}
                  isCompleted={false}
                  onToggle={(id) => toggleHabit.mutate(id)}
                  onOpen={setSelectedHabitId}
                  isLoading={
                    toggleHabit.isPending &&
                    toggleHabit.variables === habit.id
                  }
                  isDisabled={!isToday}
                  maxStreak={maxStreak}
                />
              ))}

              {/* Completed */}
              {filteredHabits.completed.map((habit) => (
                <HabitCard
                  key={habit.id}
                  habit={habit}
                  isCompleted={true}
                  onToggle={(id) => toggleHabit.mutate(id)}
                  onOpen={setSelectedHabitId}
                  isLoading={
                    toggleHabit.isPending &&
                    toggleHabit.variables === habit.id
                  }
                  isDisabled={!isToday}
                  maxStreak={maxStreak}
                />
              ))}
            </div>
          </LayoutGroup>
        )}
      </div>
    </div>

        {/* Right column: Dashboard */}
        <TodayDashboard 
          maxStreak={maxStreak} 
          totalHabitsCount={all.length}
          bestStreakHabit={bestStreakHabit}
          onOpenBestHabit={() => {
            if (bestStreakHabit) {
              setSelectedHabitId(bestStreakHabit.id);
              setOpenBestStreak(true);
            }
          }}
          completed={completed}
          progress={progress}
          isDashboardExpanded={isDashboardExpanded}
          onToggleExpanded={() => setIsDashboardExpanded(!isDashboardExpanded)}
          onOpenHabit={(habitId) => setSelectedHabitId(habitId)}
        />
      </div>

      {/* Habit Details Modal */}
      {selectedHabit && (
        <HabitDetailsModal
          habit={selectedHabit}
          open={!!selectedHabitId}
          onOpenChange={(open) => {
            if (!open) {
              setSelectedHabitId(null);
              setOpenBestStreak(false);
            }
          }}
          userTimezone={currentUser?.timezone || "UTC"}
          isBestStreak={openBestStreak}
        />
      )}
    </Fragment>
  );
}
