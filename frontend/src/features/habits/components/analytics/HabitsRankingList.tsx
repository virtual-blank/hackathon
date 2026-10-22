import { useState } from "react";
import type { HabitAnalyticsSchema } from "@/api/generated/model";
import { ChevronUp, ChevronDown, ArrowUp, ArrowDown } from "lucide-react";
import { cn } from "@/shared/lib/utils";

type HabitsRankingListProps = {
  habits: HabitAnalyticsSchema[];
  onClickHabit: (habitId: string) => void;
};

type SortKey = "completion_rate" | "current_streak" | "pushes_count" | "shames_count";

type SortButtonProps = {
  label: string;
  field: SortKey;
  sortKey: SortKey;
  sortAsc: boolean;
  onClick: (key: SortKey) => void;
};

function SortButton({ label, field, sortKey, sortAsc, onClick }: SortButtonProps) {
  return (
    <button
      onClick={() => onClick(field)}
      className={cn(
        "inline-flex items-center gap-1 text-xs font-medium transition-colors",
        sortKey === field ? "text-foreground" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {label}
      {sortKey === field &&
        (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
    </button>
  );
}

export function HabitsRankingList({ habits, onClickHabit }: HabitsRankingListProps) {
  const [sortKey, setSortKey] = useState<SortKey>("completion_rate");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...habits].sort((a, b) => {
    const aVal = a[sortKey] ?? 0;
    const bVal = b[sortKey] ?? 0;
    return sortAsc ? aVal - bVal : bVal - aVal;
  });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  return (
    <div className="col-span-1 md:col-span-2 2xl:col-span-1 rounded-[16px] bg-surface border border-border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-display text-base font-medium">Рейтинг привычек</h4>
        <div className="flex items-center gap-3">
          <SortButton label="Выполнено" field="completion_rate" sortKey={sortKey} sortAsc={sortAsc} onClick={toggleSort} />
          <SortButton label="Стрик" field="current_streak" sortKey={sortKey} sortAsc={sortAsc} onClick={toggleSort} />
        </div>
      </div>

      <div className="space-y-2 max-h-[320px] overflow-y-auto">
        {sorted.map((habit, index) => (
          <button
            key={habit.habit_id}
            onClick={() => onClickHabit(habit.habit_id)}
            className="w-full flex items-center gap-3 p-3 rounded-[10px] bg-surface-muted hover:bg-muted transition-colors text-left"
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm tabular-nums"
              style={{
                backgroundColor: `${habit.color_hex}22`,
                color: habit.color_hex,
              }}
            >
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{habit.title}</p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>{habit.completion_rate}% выполнено</span>
                <span>Стрик: {habit.current_streak}</span>
              </div>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-muted-foreground shrink-0 tabular-nums">
              <span title="Пушей" className="inline-flex items-center gap-0.5">
                <ArrowUp className="w-3.5 h-3.5 text-success shrink-0" strokeWidth={2}/>
                {habit.pushes_count ?? 0}
              </span>
              <span title="Шеймов" className="inline-flex items-center gap-0.5">
                <ArrowDown className="w-3.5 h-3.5 text-destructive shrink-0" strokeWidth={2}/>
                {habit.shames_count ?? 0}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
