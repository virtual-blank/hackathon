import { useMediaQuery } from "@/shared/hooks/use-media-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
} from "@/shared/ui/drawer";
import { HabitForm } from "./HabitForm";
import type { HabitCreateFormData } from "../lib/schemas";
import { useCreateHabitApiV1HabitsPost } from "@/api/generated/🏃-habits/🏃-habits";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useAppShellStore } from "@/shared/lib/app-shell-store";

export function CreateHabitSheet() {
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const queryClient = useQueryClient();
  const { createHabitSheetOpen, setCreateHabitSheetOpen } = useAppShellStore();

  const createMutation = useCreateHabitApiV1HabitsPost();

  const handleSubmit = async (data: HabitCreateFormData) => {
    try {
      await createMutation.mutateAsync({ data });
      
      // Invalidate queries
      queryClient.invalidateQueries({
        queryKey: ["/api/v1/habits/logs/uncompleted"],
      });
      queryClient.invalidateQueries({
        queryKey: ["/api/v1/habits"],
      });

      toast.success("Привычка создана!");
      setCreateHabitSheetOpen(false);
    } catch {
      toast.error("Не удалось создать привычку. Попробуйте ещё раз.");
    }
  };

  if (isDesktop) {
    return (
      <Dialog open={createHabitSheetOpen} onOpenChange={setCreateHabitSheetOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Новая привычка</DialogTitle>
          </DialogHeader>
          <HabitForm
            onSubmit={handleSubmit}
            isLoading={createMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Drawer open={createHabitSheetOpen} onOpenChange={setCreateHabitSheetOpen}>
      <DrawerContent className="max-h-[85vh] px-4 pb-8">
        <DrawerHeader>
          <DrawerTitle>Новая привычка</DrawerTitle>
        </DrawerHeader>
        <div className="overflow-y-auto px-1">
          <HabitForm
            onSubmit={handleSubmit}
            isLoading={createMutation.isPending}
          />
        </div>
      </DrawerContent>
    </Drawer>
  );
}

