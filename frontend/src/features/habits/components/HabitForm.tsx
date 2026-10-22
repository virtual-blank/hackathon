import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch } from "react-hook-form";
import { Button } from "@/shared/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import {
  habitCreateSchema,
  type HabitCreateFormData,
} from "../lib/schemas";
import { DEFAULT_HABIT_COLORS } from "../lib/utils";
import { Visibility } from "@/api/generated/model";
import { cn } from "@/shared/lib/utils";
import { X, Plus } from "lucide-react";

type HabitFormProps = {
  mode?: "create" | "edit";
  onSubmit: (data: HabitCreateFormData) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  defaultValues?: Partial<HabitCreateFormData>;
};

export function HabitForm({
  mode = "create",
  onSubmit,
  onCancel,
  isLoading,
  defaultValues,
}: HabitFormProps) {
  const form = useForm<HabitCreateFormData>({
    resolver: zodResolver(habitCreateSchema),
    defaultValues: {
      title: "",
      color_hex: DEFAULT_HABIT_COLORS[0],
      visibility: Visibility.private,
      notification_times: [],
      ...defaultValues,
    },
  });

  const currentColor = useWatch({ control: form.control, name: "color_hex" });
  const colorPalette = currentColor && !DEFAULT_HABIT_COLORS.includes(currentColor)
    ? [currentColor, ...DEFAULT_HABIT_COLORS]
    : DEFAULT_HABIT_COLORS;

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Title */}
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Название</FormLabel>
              <FormControl>
                <Input
                  placeholder="Например: Пробежка, Медитация"
                  {...field}
                  maxLength={100}
                  disabled={isLoading}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Color picker */}
        <FormField
          control={form.control}
          name="color_hex"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Цвет</FormLabel>
              <FormControl>
                <div className="flex flex-wrap gap-2">
                  {colorPalette.map((color) => (
                    <button
                      key={color}
                      type="button"
                      disabled={isLoading}
                      onClick={() => field.onChange(color)}
                      className={cn(
                        "w-10 h-10 rounded-full transition-all",
                        "hover:scale-110 disabled:opacity-50",
                        field.value === color
                          ? "ring-2 ring-offset-2 ring-primary scale-110"
                          : ""
                      )}
                      style={{ backgroundColor: color }}
                    >
                      <span className="sr-only">{color}</span>
                    </button>
                  ))}
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Visibility */}
        <FormField
          control={form.control}
          name="visibility"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Видимость</FormLabel>
              <FormControl>
                <div className="flex flex-col gap-2">
                  {[
                    {
                      value: Visibility.private,
                      label: "Приватная",
                      description: "Только для вас",
                    },
                    {
                      value: Visibility.friends,
                      label: "Для друзей",
                      description: "Друзья видят в ленте",
                    },
                    {
                      value: Visibility.public,
                      label: "Публичная",
                      description: "Все видят в ленте",
                    },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      disabled={isLoading}
                      onClick={() => field.onChange(option.value)}
                      className={cn(
                        "p-3 rounded-xl border text-left transition-all",
                        "hover:border-primary/50",
                        field.value === option.value
                          ? "border-primary bg-primary/5"
                          : "border-border"
                      )}
                    >
                      <div className="font-medium text-sm">{option.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    </button>
                  ))}
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Notification Times */}
        <FormField
          control={form.control}
          name="notification_times"
          render={({ field }) => {
            const times = field.value || [];
            
            const addTime = () => {
              if (times.length < 3) {
                field.onChange([...times, ""]);
              }
            };

            const removeTime = (index: number) => {
              field.onChange(times.filter((_, i) => i !== index));
            };

            const updateTime = (index: number, value: string) => {
              const newTimes = [...times];
              newTimes[index] = value;
              field.onChange(newTimes.sort());
            };

            return (
              <FormItem>
                <FormLabel>Напоминания</FormLabel>
                <FormControl>
                  <div className="space-y-2">
                    {times.map((time, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Input
                          type="time"
                          value={time}
                          onChange={(e) => updateTime(index, e.target.value)}
                          disabled={isLoading}
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeTime(index)}
                          disabled={isLoading}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                    {times.length < 3 && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addTime}
                        disabled={isLoading}
                        className="gap-2"
                      >
                        <Plus className="w-4 h-4" />
                        Добавить время
                      </Button>
                    )}
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            );
          }}
        />

        {/* Submit */}
        <div className="flex gap-2 pt-4">
          {mode === "edit" && onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
              size="lg"
              className="flex-1"
            >
              Отмена
            </Button>
          )}
          <Button
            type="submit"
            className="flex-1"
            disabled={isLoading}
            size="lg"
          >
            {isLoading
              ? mode === "edit"
                ? "Сохраняем..."
                : "Создаём..."
              : mode === "edit"
                ? "Сохранить"
                : "Создать привычку"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
