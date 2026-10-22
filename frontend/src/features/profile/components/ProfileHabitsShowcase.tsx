import { useState } from "react";
import { Flame } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import type { HabitOutputSchema } from "@/api/generated/model";
import { EmptyState } from "@/shared/components/EmptyState";
import { useAppShellStore } from "@/shared/lib/app-shell-store";

type ProfileHabitsShowcaseProps = {
  habits: HabitOutputSchema[];
  privateCount: number;
};

export function ProfileHabitsShowcase({ habits, privateCount }: ProfileHabitsShowcaseProps) {
  const [showAll, setShowAll] = useState(false);
  const { setCreateHabitSheetOpen } = useAppShellStore();
  
  const visibleHabits = showAll ? habits : habits.slice(0, 5);
  const hasMore = habits.length > 5;

  if (habits.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="font-display text-2xl font-semibold px-4">Витрина привычек</h2>
        <EmptyState
          title="Нет видимых привычек"
          description="Привычки с выбранной видимостью отсутствуют. Измените настройки видимости в разделе Привычки."
          actionLabel="Создать привычку"
          onAction={() => setCreateHabitSheetOpen(true)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-4">
        <h2 className="font-display text-2xl font-semibold">Витрина привычек</h2>
        {hasMore && !showAll && (
          <Button variant="ghost" size="sm" onClick={() => setShowAll(true)}>
            Показать все
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 px-4">
        {visibleHabits.map((habit) => {
          const isMilestone = habit.current_streak_days > 0 && habit.current_streak_days % 7 === 0;

          return (
            <div
              key={habit.id}
              className="relative p-4 rounded-[12px] border transition-all motion-reduce:transition-none"
              style={{
                borderColor: `color-mix(in srgb, ${habit.color_hex} 22%, transparent)`,
                boxShadow: `0 4px 18px color-mix(in srgb, ${habit.color_hex} 12%, transparent)`,
              }}
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-[15px] truncate">{habit.title}</h3>
                  {habit.current_streak_days > 0 && (
                    <div className="flex items-center gap-1.5 mt-1">
                      <Flame
                        className={cn(
                          "w-4 h-4",
                          isMilestone ? "text-streak" : "text-muted-foreground"
                        )}
                        strokeWidth={1.75}
                      />
                      <span className="text-sm text-muted-foreground tabular-nums">
                        {habit.current_streak_days} дн.
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {privateCount > 0 && (
        <p className="text-sm text-muted-foreground text-center px-4">
          {privateCount} {privateCount === 1 ? "приватная привычка скрыта" : "приватных привычек скрыты"} от других
        </p>
      )}
    </div>
  );
}
