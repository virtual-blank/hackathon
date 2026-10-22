import { useState, useMemo, useEffect } from "react";
import { useMediaQuery } from "@/shared/hooks/use-media-query";
import type { HabitOutputSchema } from "@/api/generated/model";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/shared/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerTitle,
  DrawerDescription,
} from "@/shared/ui/drawer";
import { HabitDetailsView } from "./HabitDetailsView";
import { HabitForm } from "./HabitForm";
import { 
  useUpdateHabitApiV1HabitsHabitIdPatch,
  useDeleteHabitApiV1HabitsHabitIdDelete
} from "@/api/generated/🏃-habits/🏃-habits";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import type { HabitCreateFormData } from "../lib/schemas";
import confetti from "canvas-confetti";
import { Flame } from "lucide-react";
import { motion } from "motion/react";

type HabitDetailsModalProps = {
  habit: HabitOutputSchema;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userTimezone: string;
  isBestStreak?: boolean;
};

export function HabitDetailsModal({
  habit,
  open,
  onOpenChange,
  userTimezone,
  isBestStreak = false,
}: HabitDetailsModalProps) {
  const [mode, setMode] = useState<"view" | "edit">("view");
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const queryClient = useQueryClient();
  
  const updateMutation = useUpdateHabitApiV1HabitsHabitIdPatch();
  const deleteMutation = useDeleteHabitApiV1HabitsHabitIdDelete();

  // Confetti on best streak modal open
  useEffect(() => {
    if (open && isBestStreak) {
      const shouldAnimate = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (shouldAnimate) {
        confetti({
          particleCount: 55,
          spread: 60,
          scalar: 0.9,
          ticks: 140,
          colors: ['#F97316', '#F59E0B', '#FBBF24', '#10B981'],
          origin: { y: 0.4 }
        });
      }
    }
  }, [open, isBestStreak]);

  const handleEdit = () => setMode("edit");
  const handleCancelEdit = () => setMode("view");

  const handleDelete = async () => {
    if (!window.confirm(`Вы действительно хотите удалить привычку "${habit.title}"?`)) {
      return;
    }

    try {
      await deleteMutation.mutateAsync({ habitId: habit.id });
      
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs/completed"] });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs/uncompleted"] });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs"] });
      
      toast.success("Привычка удалена");
      onOpenChange(false);
    } catch {
      toast.error("Не удалось удалить привычку");
    }
  };

  const handleUpdate = async (data: HabitCreateFormData) => {
    const changes: Record<string, unknown> = {};
    
    if (data.title !== habit.title) changes.title = data.title;
    if (data.color_hex !== habit.color_hex) changes.color_hex = data.color_hex;
    if (data.visibility !== habit.visibility) changes.visibility = data.visibility;
    
    const oldTimes = (habit.notification_times || []).map((t) => t.slice(0, 5)).sort();
    const newTimes = (data.notification_times || []).sort();
    if (JSON.stringify(oldTimes) !== JSON.stringify(newTimes)) {
      changes.notification_times = newTimes;
    }

    if (Object.keys(changes).length === 0) {
      setMode("view");
      return;
    }

    try {
      await updateMutation.mutateAsync({
        habitId: habit.id,
        data: changes,
      });
      
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs/completed"] });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs/uncompleted"] });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/habits/logs"] });
      
      toast.success("Изменения сохранены");
      setMode("view");
    } catch {
      toast.error("Не удалось сохранить изменения");
    }
  };

  const editDefaultValues = useMemo<HabitCreateFormData>(
    () => ({
      title: habit.title,
      color_hex: habit.color_hex,
      visibility: habit.visibility,
      notification_times: (habit.notification_times || []).map((t) => t.slice(0, 5)),
    }),
    [habit]
  );

  const content = (
    <>
      {isBestStreak && mode === "view" && (
        <motion.div
          initial={{ opacity: 0, y: -12, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className="mb-4 rounded-[12px] bg-gradient-to-r from-streak/10 to-transparent border border-streak/30 px-4 py-3 flex items-center gap-3"
        >
          <div className="rounded-full bg-streak/20 p-2">
            <Flame size={20} className="text-streak" strokeWidth={2} />
          </div>
          <p className="font-semibold text-foreground">Лучший стрик!</p>
        </motion.div>
      )}
      
      {mode === "view" ? (
        <HabitDetailsView
          habit={habit}
          userTimezone={userTimezone}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ) : (
        <HabitForm
          mode="edit"
          defaultValues={editDefaultValues}
          onSubmit={handleUpdate}
          onCancel={handleCancelEdit}
          isLoading={updateMutation.isPending}
        />
      )}
    </>
  );

  if (isDesktop) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent
          className="max-w-2xl max-h-[90vh] overflow-y-auto"
          overlayClassName="glass-overlay"
        >
          <DialogTitle className="sr-only">{habit.title}</DialogTitle>
          <DialogDescription className="sr-only">
            Подробности о привычке {habit.title}
          </DialogDescription>
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent
        className="max-h-[90vh] overflow-y-auto px-4 pb-safe-area-inset-bottom"
        overlayClassName="glass-overlay"
      >
        <DrawerTitle className="sr-only">{habit.title}</DrawerTitle>
        <DrawerDescription className="sr-only">
          Подробности о привычке {habit.title}
        </DrawerDescription>
        <div className="py-4">{content}</div>
      </DrawerContent>
    </Drawer>
  );
}
