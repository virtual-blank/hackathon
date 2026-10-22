import { cn } from "@/shared/lib/utils";
import type { AudienceType } from "../lib/profile-helpers";

type AudienceSwitchProps = {
  value: AudienceType;
  onChange: (value: AudienceType) => void;
  className?: string;
};

export function AudienceSwitch({ value, onChange, className }: AudienceSwitchProps) {
  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <span className="text-xs text-muted-foreground">Так вас видят другие</span>
      <div
        className="inline-flex items-center rounded-full bg-surface-muted p-1 gap-1"
        role="radiogroup"
        aria-label="Выбор аудитории"
      >
        <button
          type="button"
          role="radio"
          aria-checked={value === "friends"}
          onClick={() => onChange("friends")}
          className={cn(
            "relative px-4 h-8 rounded-full text-sm font-medium transition-all",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            value === "friends"
              ? "bg-surface-elevated text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Друзья
        </button>
        <button
          type="button"
          role="radio"
          aria-checked={value === "public"}
          onClick={() => onChange("public")}
          className={cn(
            "relative px-4 h-8 rounded-full text-sm font-medium transition-all",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            value === "public"
              ? "bg-surface-elevated text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Все
        </button>
      </div>
    </div>
  );
}
