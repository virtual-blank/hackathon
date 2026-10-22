import type { HabitOutputSchema, WeekdayActivitySchema } from "@/api/generated/model";
import { getBestHabit, getFavoriteWeekday, getAccountAge, getWeekdayName } from "../lib/profile-helpers";
import { pluralizeDays } from "@/shared/lib/date";
import { pluralize } from "@/shared/lib/pluralize";

type ProfileHighlightsProps = {
  visibleHabits: HabitOutputSchema[];
  weekdayActivity: WeekdayActivitySchema[];
  userCreatedAt: string;
};

export function ProfileHighlights({
  visibleHabits,
  weekdayActivity,
  userCreatedAt,
}: ProfileHighlightsProps) {
  const bestHabit = getBestHabit(visibleHabits);
  const favoriteWeekday = getFavoriteWeekday(weekdayActivity);
  const accountAge = getAccountAge(userCreatedAt);

  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl font-semibold px-4">Хайлайты</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-4">
        {/* Best habit */}
        <div className="p-4 rounded-[16px] bg-surface border border-border space-y-2">
          <h3 className="text-sm text-muted-foreground">Самая стойкая привычка</h3>
          {bestHabit ? (
            <>
              <p className="font-medium text-foreground">{bestHabit.title}</p>
              <p className="text-sm text-muted-foreground">
                Рекорд: {bestHabit.max_streak_days} {pluralizeDays(bestHabit.max_streak_days)}
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Пока недостаточно данных</p>
          )}
        </div>

        {/* Favorite weekday */}
        <div className="p-4 rounded-[16px] bg-surface border border-border space-y-2">
          <h3 className="text-sm text-muted-foreground">Любимый день недели</h3>
          {favoriteWeekday && favoriteWeekday.completed_count > 0 ? (
            <>
              <p className="font-medium text-foreground capitalize">
                {getWeekdayName(favoriteWeekday.weekday_num)}
              </p>
              <p className="text-sm text-muted-foreground">
                {favoriteWeekday.completed_count}{" "}
                {pluralize(favoriteWeekday.completed_count, "выполнение", "выполнения", "выполнений")}
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Пока недостаточно данных</p>
          )}
        </div>

        {/* Account age */}
        <div className="p-4 rounded-[16px] bg-surface border border-border space-y-2">
          <h3 className="text-sm text-muted-foreground">Стаж</h3>
          <p className="font-medium text-foreground">
            {accountAge} {pluralizeDays(accountAge)}
          </p>
          <p className="text-sm text-muted-foreground">С нами</p>
        </div>
      </div>
    </div>
  );
}
