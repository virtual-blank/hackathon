import { useState } from "react";
import { Filter, Calendar } from "lucide-react";
import { Button } from "@/shared/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/shared/ui/popover";

type FilterStatus = "all" | "completed" | "uncompleted";

type TodayFiltersProps = {
  status: FilterStatus;
  date: string;
  onStatusChange: (status: FilterStatus) => void;
  onDateChange: (date: string) => void;
};

export function TodayFilters({
  status,
  date,
  onStatusChange,
  onDateChange,
}: TodayFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);

  const statusLabels: Record<FilterStatus, string> = {
    all: "Все",
    completed: "Выполнено",
    uncompleted: "В процессе",
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="default" className="gap-2">
          <Filter size={16} strokeWidth={1.75} />
          Фильтровать
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-56">
        <div className="space-y-4">
          {/* Status */}
          <div className="space-y-2">
            <div className="text-sm font-medium">Статус</div>
            <div className="space-y-1">
              {(["all", "completed", "uncompleted"] as FilterStatus[]).map((s) => (
                <button
                  key={s}
                  onClick={() => onStatusChange(s)}
                  className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                    status === s
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                >
                  {statusLabels[s]}
                </button>
              ))}
            </div>
          </div>

          {/* Date */}
          <div className="space-y-2">
            <label className="text-sm font-medium block">Дата</label>
            <div className="relative">
              <input
                type="date"
                value={date}
                onChange={(e) => onDateChange(e.target.value)}
                className="w-full h-9 px-3 pr-8 text-sm rounded-md border border-border bg-surface-muted focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" strokeWidth={1.75} />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
