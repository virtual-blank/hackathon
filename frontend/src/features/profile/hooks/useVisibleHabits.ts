import { useMemo } from "react";
import type { HabitOutputSchema } from "@/api/generated/model";
import { filterVisibleHabits, sortHabitsByStreak, type AudienceType } from "../lib/profile-helpers";

type UseVisibleHabitsParams = {
  habits: HabitOutputSchema[] | undefined;
  audience: AudienceType;
};

export function useVisibleHabits({ habits, audience }: UseVisibleHabitsParams) {
  return useMemo(() => {
    if (!habits) return [];
    const visible = filterVisibleHabits(habits, audience);
    return sortHabitsByStreak(visible);
  }, [habits, audience]);
}
