import { Check } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/shared/lib/utils";
import { useState } from "react";

type HabitCheckboxProps = {
  checked: boolean;
  disabled: boolean;
  habitTitle: string;
  onClick: () => void;
};

export function HabitCheckbox({
  checked,
  disabled,
  habitTitle,
  onClick,
}: HabitCheckboxProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={`Отметить «${habitTitle}»`}
      disabled={disabled}
      onClick={onClick}
      onHoverStart={() => !disabled && setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={cn(
        "size-7 rounded-full flex items-center justify-center flex-shrink-0",
        "transition-all duration-200",
        "disabled:cursor-not-allowed disabled:opacity-50",
        checked
          ? "bg-primary border-primary"
          : "bg-surface-muted border-[1px] border-border"
      )}
      whileHover={!disabled ? { scale: 1.12 } : {}}
      whileTap={!disabled ? { scale: 0.95 } : {}}
      animate={checked ? { scale: [1, 1.18, 1] } : {}}
      transition={{ duration: checked ? 0.4 : 0.2 }}
    >
      <AnimatePresence mode="wait">
        {checked ? (
          <motion.div
            key="checked"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="motion-reduce:transition-none motion-reduce:animate-none"
          >
            <Check className="w-4 h-4 text-primary-foreground" strokeWidth={2.5} />
          </motion.div>
        ) : isHovered ? (
          <motion.div
            key="hover"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 0.35 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="motion-reduce:opacity-0"
          >
            <Check className="w-4 h-4 text-muted-foreground" strokeWidth={2.5} />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.button>
  );
}
