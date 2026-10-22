import { useMemo } from "react";
import { startOfWeek, addDays, format, parseISO } from "date-fns";
import { ru } from "date-fns/locale";
import { cn } from "@/shared/lib/utils";

type HeatCell = {
  date: string;
  level: 0 | 1 | 2 | 3 | 4;
};

type ActivityHeatmapProps = {
  cells: HeatCell[];
  weeksToShow?: number;
  className?: string;
  showLegend?: boolean;
};

export function ActivityHeatmap({
  cells,
  weeksToShow = 26,
  className,
  showLegend = true,
}: ActivityHeatmapProps) {
  const { grid, monthLabels } = useMemo(() => {
    const cellMap = new Map(cells.map((c) => [c.date, c.level]));
    
    // Calculate date range
    const endDate = new Date();
    const startDate = addDays(endDate, -(weeksToShow * 7 - 1));
    const firstWeekStart = startOfWeek(startDate, { weekStartsOn: 1 }); // Monday

    // Build grid: array of weeks, each week is array of 7 days
    const weeks: Array<Array<{ date: string; level: 0 | 1 | 2 | 3 | 4 }>> = [];
    let currentWeekStart = firstWeekStart;

    for (let w = 0; w < weeksToShow; w++) {
      const week: Array<{ date: string; level: 0 | 1 | 2 | 3 | 4 }> = [];
      for (let d = 0; d < 7; d++) {
        const dayDate = addDays(currentWeekStart, d);
        const dateStr = format(dayDate, "yyyy-MM-dd");
        const isFuture = dayDate > endDate;
        
        week.push({
          date: dateStr,
          level: isFuture ? 0 : (cellMap.get(dateStr) ?? 0),
        });
      }
      weeks.push(week);
      currentWeekStart = addDays(currentWeekStart, 7);
    }

    // Month labels: show month name when it starts in that week column
    const labels: Array<{ week: number; label: string }> = [];
    let lastMonth = -1;
    weeks.forEach((week, weekIdx) => {
      const firstDayOfWeek = week[0].date;
      const monthNum = parseInt(format(parseISO(firstDayOfWeek), "M"), 10);
      if (monthNum !== lastMonth) {
        labels.push({
          week: weekIdx,
          label: format(parseISO(firstDayOfWeek), "MMM", { locale: ru }),
        });
        lastMonth = monthNum;
      }
    });

    return { grid: weeks, monthLabels: labels };
  }, [cells, weeksToShow]);

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      {/* Center the entire heatmap (labels + grid + legend) */}
      <div className="w-fit mx-auto">
        {/* Month labels */}
        <div className="flex mb-1 relative" style={{ height: "16px" }}>
          {monthLabels.map(({ week, label }) => (
            <div
              key={week}
              className="absolute text-xs text-muted-foreground"
              style={{ left: `${week * 14 + 20}px` }}
            >
              {label}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="flex gap-[2px]">
          {/* Day labels */}
          <div className="flex flex-col gap-[2px] mr-1">
            {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((day, idx) => (
              <div
                key={day}
                className={cn(
                  "text-[10px] leading-none text-muted-foreground flex items-center",
                  idx % 2 !== 0 && "opacity-0"
                )}
                style={{ height: "12px" }}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Week columns */}
          {grid.map((week, weekIdx) => (
            <div key={weekIdx} className="flex flex-col gap-[2px]">
              {week.map((cell) => {
                const cellDate = parseISO(cell.date);
                const isFuture = cellDate > new Date();
                const colorClass = isFuture
                  ? ""
                  : cell.level === 4
                    ? "bg-heat-4"
                    : cell.level === 3
                      ? "bg-heat-3"
                      : cell.level === 2
                        ? "bg-heat-2"
                        : cell.level === 1
                          ? "bg-heat-1"
                          : "bg-heat-0";
                
                return (
                  <div
                    key={cell.date}
                    className={cn(
                      "rounded-[3px] transition-colors",
                      isFuture ? "opacity-0" : colorClass
                    )}
                    style={{ width: "12px", height: "12px" }}
                    title={`${format(cellDate, "d MMM", { locale: ru })} — ${
                      cell.level > 0 ? "выполнено" : "не выполнено"
                    }`}
                  />
                );
              })}
            </div>
          ))}
        </div>

        {/* Legend */}
        {showLegend && (
          <div className="flex items-center gap-1 mt-2 text-[10px] text-muted-foreground">
            <span>Активность:</span>
            {[0, 1, 2, 3, 4].map((level) => (
              <div
                key={level}
                className={cn(
                  "w-3 h-3 rounded-[2px]",
                  level === 4
                    ? "bg-heat-4"
                    : level === 3
                      ? "bg-heat-3"
                      : level === 2
                        ? "bg-heat-2"
                        : level === 1
                          ? "bg-heat-1"
                          : "bg-heat-0"
                )}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
