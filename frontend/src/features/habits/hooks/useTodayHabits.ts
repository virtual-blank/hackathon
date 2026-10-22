import { useMemo } from "react";
import {
  useGetCompletedHabitsApiV1HabitsLogsCompletedGet,
  useGetUncompletedHabitsApiV1HabitsLogsUncompletedGet,
} from "@/api/generated/🏃-habits/🏃-habits";
import type { HabitOutputSchema } from "@/api/generated/model";
import { calculateProgress, getMaxStreak } from "../lib/utils";

type UseTodayHabitsReturn = {
  completed: HabitOutputSchema[];
  uncompleted: HabitOutputSchema[];
  all: HabitOutputSchema[];
  progress: number;
  maxStreak: number;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
};

export function useTodayHabits(date: string): UseTodayHabitsReturn {
  const completedQuery = useGetCompletedHabitsApiV1HabitsLogsCompletedGet({
    target_date: date,
  });

  const uncompletedQuery = useGetUncompletedHabitsApiV1HabitsLogsUncompletedGet(
    { target_date: date }
  );

  const isLoading = completedQuery.isLoading || uncompletedQuery.isLoading;
  const isError = completedQuery.isError || uncompletedQuery.isError;
  const error = completedQuery.error || uncompletedQuery.error;

  const completed = useMemo(
    () => completedQuery.data ?? [],
    [completedQuery.data]
  );
  const uncompleted = useMemo(
    () => uncompletedQuery.data ?? [],
    [uncompletedQuery.data]
  );
  const all = useMemo(
    () => [...completed, ...uncompleted],
    [completed, uncompleted]
  );

  const progress = useMemo(
    () => calculateProgress(completed.length, all.length),
    [completed.length, all.length]
  );

  const maxStreak = useMemo(() => getMaxStreak(all), [all]);

  const refetch = () => {
    completedQuery.refetch();
    uncompletedQuery.refetch();
  };

  return {
    completed,
    uncompleted,
    all,
    progress,
    maxStreak,
    isLoading,
    isError,
    error,
    refetch,
  };
}
