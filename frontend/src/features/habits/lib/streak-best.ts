import type { HabitOutputSchema } from "@/api/generated/model";

/**
 * Select the habit with the best streak in a deterministic way.
 * Tie-breaker: current_streak_days desc, then max_streak_days desc, then created_at asc (earliest).
 * Does not depend on array order or title.
 */
export function getBestStreakHabit(
  habits: HabitOutputSchema[]
): HabitOutputSchema | null {
  if (habits.length === 0) return null;

  // Find habit with max current_streak_days > 0
  const withActiveStreak = habits.filter((h) => h.current_streak_days > 0);
  if (withActiveStreak.length > 0) {
    return withActiveStreak.reduce((best, h) => {
      if (h.current_streak_days > best.current_streak_days) return h;
      if (h.current_streak_days < best.current_streak_days) return best;
      // Tie: same current_streak_days
      if (h.max_streak_days > best.max_streak_days) return h;
      if (h.max_streak_days < best.max_streak_days) return best;
      // Tie: same max_streak_days, use created_at (earliest wins)
      return new Date(h.created_at) < new Date(best.created_at) ? h : best;
    });
  }

  // Fallback: max historical streak if no active streaks
  return habits.reduce((best, h) => {
    if (h.max_streak_days > best.max_streak_days) return h;
    if (h.max_streak_days < best.max_streak_days) return best;
    // Tie: same max_streak, use created_at
    return new Date(h.created_at) < new Date(best.created_at) ? h : best;
  });
}
