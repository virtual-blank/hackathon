import { useGetLogsInRangeApiV1HabitsLogsGet } from "@/api/generated/🏃-habits/🏃-habits";

type UseHabitLogsParams = {
  habitId: string;
  startDate: string;
  endDate: string;
};

export function useHabitLogs({ habitId, startDate, endDate }: UseHabitLogsParams) {
  return useGetLogsInRangeApiV1HabitsLogsGet({
    date_from: startDate,
    date_to: endDate,
    habit_id: habitId,
    limit: 1000,
  });
}
