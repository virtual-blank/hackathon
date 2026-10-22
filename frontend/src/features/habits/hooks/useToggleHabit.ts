import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  useMarkHabitApiV1HabitsHabitIdTogglePatch,
  getGetCompletedHabitsApiV1HabitsLogsCompletedGetQueryKey,
  getGetUncompletedHabitsApiV1HabitsLogsUncompletedGetQueryKey,
} from "@/api/generated/🏃-habits/🏃-habits";
import { toast } from "sonner";
import confetti from "canvas-confetti";
import type { HabitOutputSchema } from "@/api/generated/model";

type UseToggleHabitOptions = {
  date: string;
  onSuccess?: (habit: HabitOutputSchema, wasCompleted: boolean) => void;
};

export function useToggleHabit({ date, onSuccess }: UseToggleHabitOptions) {
  const queryClient = useQueryClient();
  const toggleMutation = useMarkHabitApiV1HabitsHabitIdTogglePatch();

  return useMutation({
    mutationFn: async (habitId: string) => {
      return toggleMutation.mutateAsync({ habitId });
    },
    onMutate: async (habitId) => {
      const completedKey = getGetCompletedHabitsApiV1HabitsLogsCompletedGetQueryKey({ target_date: date });
      const uncompletedKey = getGetUncompletedHabitsApiV1HabitsLogsUncompletedGetQueryKey({ target_date: date });

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: completedKey });
      await queryClient.cancelQueries({ queryKey: uncompletedKey });

      // Snapshot previous values
      const previousCompleted = queryClient.getQueryData<HabitOutputSchema[]>(completedKey);
      const previousUncompleted = queryClient.getQueryData<HabitOutputSchema[]>(uncompletedKey);

      // Optimistically update: move habit between lists
      if (previousCompleted && previousUncompleted) {
        const habitInCompleted = previousCompleted.find(
          (h) => h.id === habitId
        );
        const habitInUncompleted = previousUncompleted.find(
          (h) => h.id === habitId
        );

        if (habitInCompleted) {
          // Move from completed to uncompleted
          queryClient.setQueryData<HabitOutputSchema[]>(
            completedKey,
            previousCompleted.filter((h) => h.id !== habitId)
          );
          queryClient.setQueryData<HabitOutputSchema[]>(
            uncompletedKey,
            [...previousUncompleted, habitInCompleted]
          );
        } else if (habitInUncompleted) {
          // Move from uncompleted to completed
          queryClient.setQueryData<HabitOutputSchema[]>(
            uncompletedKey,
            previousUncompleted.filter((h) => h.id !== habitId)
          );
          queryClient.setQueryData<HabitOutputSchema[]>(
            completedKey,
            [...previousCompleted, habitInUncompleted]
          );
        }
      }

      return { previousCompleted, previousUncompleted };
    },
    onSuccess: (response) => {
      const { habit, is_completed } = response;

      const completedKey = getGetCompletedHabitsApiV1HabitsLogsCompletedGetQueryKey({ target_date: date });
      const uncompletedKey = getGetUncompletedHabitsApiV1HabitsLogsUncompletedGetQueryKey({ target_date: date });

      // Invalidate queries to get fresh data from server
      queryClient.invalidateQueries({ queryKey: completedKey });
      queryClient.invalidateQueries({ queryKey: uncompletedKey });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs"] });
      
      // Invalidate dashboard analytics
      queryClient.invalidateQueries({ queryKey: ["/api/v1/analytics/dashboard"] });

      // Show toast
      if (is_completed) {
        toast.success("Привычка отмечена!");
      } else {
        toast.info("Отметка снята");
      }

      // Confetti on milestone streaks (multiples of 7)
      if (
        is_completed &&
        habit.current_streak_days > 0 &&
        habit.current_streak_days % 7 === 0
      ) {
        const shouldAnimate = !window.matchMedia(
          "(prefers-reduced-motion: reduce)"
        ).matches;
        if (shouldAnimate) {
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
          });
        }
      }

      onSuccess?.(habit, is_completed);
    },
    onError: (_error, _habitId, context) => {
      const completedKey = getGetCompletedHabitsApiV1HabitsLogsCompletedGetQueryKey({ target_date: date });
      const uncompletedKey = getGetUncompletedHabitsApiV1HabitsLogsUncompletedGetQueryKey({ target_date: date });

      // Rollback on error
      if (context?.previousCompleted) {
        queryClient.setQueryData(completedKey, context.previousCompleted);
      }
      if (context?.previousUncompleted) {
        queryClient.setQueryData(uncompletedKey, context.previousUncompleted);
      }

      toast.error("Не удалось обновить привычку. Попробуйте ещё раз.");
    },
  });
}

