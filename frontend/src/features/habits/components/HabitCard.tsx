import { Flame, Clock, Lock, Users, Globe, ChevronRight } from "lucide-react";
import { motion } from "motion/react";
import { cn } from "@/shared/lib/utils";
import type { HabitOutputSchema } from "@/api/generated/model";
import { HabitCheckbox } from "./HabitCheckbox";
import { getStreakHeat, getFlameColor } from "../lib/streak";
import { pluralizeDays } from "@/shared/lib/date";

type HabitCardProps = {
  habit: HabitOutputSchema;
  isCompleted: boolean;
  onToggle: (habitId: string) => void;
  onOpen?: (habitId: string) => void;
  isLoading?: boolean;
  isDisabled?: boolean;
  maxStreak: number;
};

const visibilityIcons = {
  private: Lock,
  friends: Users,
  public: Globe,
} as const;

const visibilityLabels = {
  private: "Приватная",
  friends: "Для друзей",
  public: "Публичная",
} as const;

export function HabitCard({
  habit,
  isCompleted,
  onToggle,
  onOpen,
  isLoading,
  isDisabled = false,
  maxStreak,
}: HabitCardProps) {
  const disabled = isLoading || isDisabled;
  const hasStreak = habit.current_streak_days > 0;
  const hasRecord = habit.max_streak_days > 0 && habit.current_streak_days === 0;
  const hasNotifications = habit.notification_times.length > 0;

  const heat = getStreakHeat(habit.current_streak_days, maxStreak);
  const flameColor = getFlameColor(heat);
  
  const VisibilityIcon = visibilityIcons[habit.visibility];

  const handlePointerMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    // Spotlight works if card can be opened, regardless of checkbox disabled state
    if (isCompleted || !onOpen) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    e.currentTarget.style.setProperty('--mouse-x', `${x}px`);
    e.currentTarget.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <motion.div
      layout
      layoutId={habit.id}
      className="flex items-center gap-3"
      transition={{
        layout: { type: "spring", stiffness: 500, damping: 35, duration: 0.5 }
      }}
    >
      {/* Checkbox */}
      <HabitCheckbox
        checked={isCompleted}
        disabled={disabled}
        habitTitle={habit.title}
        onClick={() => !disabled && onToggle(habit.id)}
      />

      {/* Card */}
      <motion.button
        onClick={() => onOpen?.(habit.id)}
        disabled={!onOpen}
        onPointerMove={handlePointerMove}
        layout
        animate={{
          opacity: isCompleted ? 0.6 : 1,
        }}
        transition={{
          opacity: { duration: 0.3, delay: isCompleted ? 0.25 : 0 },
          layout: { type: "spring", stiffness: 500, damping: 35 }
        }}
        whileHover={
          onOpen && !isCompleted
            ? { scale: 1.017, transition: { duration: 0.2, ease: "easeOut" } }
            : {}
        }
        className={cn(
          "flex-1 rounded-[12px] min-h-[60px]",
          "flex items-center gap-3 px-4 py-3",
          "group/card",
          isCompleted
            ? "border border-border bg-surface shadow-none"
            : "habit-glow",
          onOpen && !disabled && "active:scale-[0.98] cursor-pointer",
          "motion-reduce:transition-none motion-reduce:hover:scale-100"
        )}
        style={
          isCompleted
            ? undefined
            : ({ ["--habit" as string]: habit.color_hex } as React.CSSProperties)
        }
      >
        {/* Left: Color indicator */}
        {!isCompleted && (
          <div
            className="w-1 h-6 rounded-full flex-shrink-0"
            style={{ backgroundColor: habit.color_hex }}
          />
        )}

        {/* Content */}
        <div className="flex-1 min-w-0 flex flex-col gap-1">
          {/* Title with strikethrough */}
          <div className="relative inline-block">
            <span
              className={cn(
                "font-sans font-semibold text-[15px] md:text-[16px] tracking-[-0.01em] text-foreground"
              )}
              role="heading"
              aria-level={3}
            >
              {habit.title}
            </span>
            {isCompleted && (
              <motion.div
                className="absolute inset-0 flex items-center pointer-events-none"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.4, ease: "easeOut", delay: 0.15 }}
                style={{ transformOrigin: "left" }}
              >
                <div className="w-full h-[1.5px] bg-foreground/40" />
              </motion.div>
            )}
          </div>

          {/* Meta info */}
          {(hasNotifications || !isCompleted) && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              {/* Visibility */}
              {!isCompleted && (
                <div className="flex items-center gap-1" title={visibilityLabels[habit.visibility]}>
                  <VisibilityIcon size={13} strokeWidth={1.75} />
                  <span className="sr-only">{visibilityLabels[habit.visibility]}</span>
                </div>
              )}

              {/* Notifications */}
              {hasNotifications && (
                <div className="flex items-center gap-1">
                  <Clock size={13} strokeWidth={1.75} />
                  <span>
                    {habit.notification_times
                      .map((time) => time.slice(0, 5))
                      .join(", ")}
                  </span>
                </div>
              )}

              {/* Record streak */}
              {hasRecord && !isCompleted && (
                <div className="flex items-center gap-1 ml-auto">
                  <span>Рекорд: {habit.max_streak_days} {pluralizeDays(habit.max_streak_days)}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Streak indicator */}
        {hasStreak && !isCompleted && (
          <div className="flex items-center gap-1.5 text-sm flex-shrink-0">
            <div
              className="rounded-full p-1 transition-all duration-200"
              style={{
                backgroundColor: `color-mix(in srgb, ${flameColor} 18%, transparent)`,
              }}
            >
              <Flame
                size={16}
                strokeWidth={1.75}
                className="flex-shrink-0"
                style={{ color: flameColor }}
              />
            </div>
            <span className="tabular-nums text-muted-foreground">
              {habit.current_streak_days} дн.
            </span>
          </div>
        )}

        {/* Chevron */}
        {onOpen && !disabled && (
          <ChevronRight
            size={16}
            strokeWidth={1.75}
            className={cn(
              "flex-shrink-0 text-muted-foreground/50",
              "transition-all duration-200",
              "group-hover/card:translate-x-0.5 group-hover/card:text-muted-foreground/70"
            )}
          />
        )}
      </motion.button>
    </motion.div>
  );
}

