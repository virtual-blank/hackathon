import { z } from "zod";
import { Visibility } from "@/api/generated/model";

const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;

export const habitCreateSchema = z.object({
  title: z
    .string()
    .min(1, "Название обязательно")
    .max(100, "Максимум 100 символов"),
  color_hex: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, "Неверный формат цвета")
    .optional(),
  visibility: z
    .enum([Visibility.private, Visibility.friends, Visibility.public])
    .optional(),
  notification_times: z
    .array(
      z
        .string()
        .regex(timeRegex, "Неверный формат времени (используйте HH:MM)")
    )
    .max(3, "Максимум 3 уведомления")
    .optional()
    .refine(
      (times) => {
        if (!times || times.length === 0) return true;
        const set = new Set(times);
        return set.size === times.length;
      },
      { message: "Время не должно повторяться" }
    ),
});

export type HabitCreateFormData = z.infer<typeof habitCreateSchema>;

