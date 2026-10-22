export const DEFAULT_HABIT_COLORS = [
  "#F97316", // orange
  "#16A34A", // success green
  "#2563EB", // info blue
  "#E11D48", // destructive red
  "#8B5CF6", // purple
  "#22D3EE", // cyan
  "#F59E0B", // amber
  "#10B981", // emerald
];

/**
 * Get today's date in YYYY-MM-DD format in the user's timezone
 * Uses Intl.DateTimeFormat to convert to user timezone, then formats to YYYY-MM-DD
 */
export function getTodayDate(timezone: string): string {
  const now = new Date();
  // Get date parts in user's timezone
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  // en-CA locale produces YYYY-MM-DD format
  return formatter.format(now);
}

/**
 * Calculate progress percentage (0-100)
 */
export function calculateProgress(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

/**
 * Get maximum streak from a list of habits
 */
export function getMaxStreak(
  habits: Array<{ current_streak_days: number }>
): number {
  if (habits.length === 0) return 0;
  return Math.max(...habits.map((h) => h.current_streak_days));
}
