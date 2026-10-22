import { differenceInDays, parseISO } from "date-fns";
import type { HabitOutputSchema, WeekdayActivitySchema } from "@/api/generated/model";
import { Visibility } from "@/api/generated/model";

export type AudienceType = "friends" | "public";

/**
 * Filters habits by visibility based on selected audience.
 */
export function filterVisibleHabits(
  habits: HabitOutputSchema[],
  audience: AudienceType
): HabitOutputSchema[] {
  if (audience === "public") {
    return habits.filter((h) => h.visibility === Visibility.public);
  }
  // audience === "friends"
  return habits.filter(
    (h) => h.visibility === Visibility.public || h.visibility === Visibility.friends
  );
}

/**
 * Counts private habits (always hidden from others).
 */
export function countPrivateHabits(habits: HabitOutputSchema[]): number {
  return habits.filter((h) => h.visibility === Visibility.private).length;
}

/**
 * Finds habit with the maximum max_streak_days among visible habits.
 */
export function getBestHabit(habits: HabitOutputSchema[]): HabitOutputSchema | null {
  if (habits.length === 0) return null;
  return habits.reduce((best, current) =>
    current.max_streak_days > best.max_streak_days ? current : best
  );
}

/**
 * Finds the weekday with the most completions.
 */
export function getFavoriteWeekday(
  weekdayActivity: WeekdayActivitySchema[]
): WeekdayActivitySchema | null {
  if (weekdayActivity.length === 0) return null;
  return weekdayActivity.reduce((best, current) =>
    current.completed_count > best.completed_count ? current : best
  );
}

/**
 * Returns the number of days since the user's account was created.
 */
export function getAccountAge(createdAt: string): number {
  return differenceInDays(new Date(), parseISO(createdAt));
}

/**
 * Returns Russian weekday name from weekday_num (0 = Monday, 6 = Sunday).
 */
export function getWeekdayName(weekdayNum: number): string {
  const names = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"];
  return names[weekdayNum] || "";
}

/**
 * Sorts habits by current_streak_days desc, then max_streak_days desc.
 */
export function sortHabitsByStreak(habits: HabitOutputSchema[]): HabitOutputSchema[] {
  return [...habits].sort((a, b) => {
    if (b.current_streak_days !== a.current_streak_days) {
      return b.current_streak_days - a.current_streak_days;
    }
    return b.max_streak_days - a.max_streak_days;
  });
}

/**
 * Finds the habit with the highest current_streak among visible habits (for glow color).
 */
export function getBrightestHabit(habits: HabitOutputSchema[]): HabitOutputSchema | null {
  if (habits.length === 0) return null;
  return habits.reduce((brightest, current) =>
    current.current_streak_days > brightest.current_streak_days ? current : brightest
  );
}
