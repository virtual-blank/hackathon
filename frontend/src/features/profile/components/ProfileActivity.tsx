import { useMemo } from "react";
import type { HabitLogOutputSchema } from "@/api/generated/model";
import { ActivityHeatmap } from "@/shared/components/ActivityHeatmap";

type ProfileActivityProps = {
  logs: HabitLogOutputSchema[];
};

type HeatCell = {
  date: string;
  level: 0 | 1 | 2 | 3 | 4;
};

function aggregateLogsByDay(logs: HabitLogOutputSchema[]): Map<string, number> {
  const dayMap = new Map<string, number>();
  
  logs.forEach((log) => {
    const day = log.completed_date;
    dayMap.set(day, (dayMap.get(day) || 0) + 1);
  });
  
  return dayMap;
}

function mapCountToLevel(count: number): 0 | 1 | 2 | 3 | 4 {
  if (count === 0) return 0;
  if (count === 1) return 1;
  if (count <= 3) return 2;
  if (count <= 5) return 3;
  return 4;
}

export function ProfileActivity({ logs }: ProfileActivityProps) {
  const cells: HeatCell[] = useMemo(() => {
    const dayMap = aggregateLogsByDay(logs);
    
    // Build cells for all unique dates in logs
    const uniqueDates = Array.from(dayMap.keys()).sort();
    
    return uniqueDates.map((date) => ({
      date,
      level: mapCountToLevel(dayMap.get(date) || 0),
    }));
  }, [logs]);

  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl font-semibold px-4">Активность за полгода</h2>
      <div className="px-4">
        <ActivityHeatmap cells={cells} weeksToShow={26} showLegend />
      </div>
    </div>
  );
}
