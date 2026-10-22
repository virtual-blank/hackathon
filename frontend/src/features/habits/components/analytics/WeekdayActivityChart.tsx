import { useState } from "react";
import type { WeekdayActivitySchema } from "@/api/generated/model";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell } from "recharts";
import { pluralize } from "@/shared/lib/pluralize";

type WeekdayActivityChartProps = {
  data: WeekdayActivitySchema[];
};

const weekdayLabels: Record<number, string> = {
  0: "Пн",
  1: "Вт",
  2: "Ср",
  3: "Чт",
  4: "Пт",
  5: "Сб",
  6: "Вс",
};

export function WeekdayActivityChart({ data }: WeekdayActivityChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const chartData = data.map((point) => ({
    weekday: weekdayLabels[point.weekday_num] || `День ${point.weekday_num}`,
    count: point.completed_count,
    weekday_name: point.weekday_name,
  }));

  const maxValue = Math.max(...data.map((d) => d.completed_count), 1);

  const totalCount = data.reduce((sum, d) => sum + d.completed_count, 0);

  return (
    <div className="col-span-1 rounded-[16px] bg-surface border border-border p-4 space-y-3">
      <h4 className="font-display text-base font-medium">Активность по дням недели</h4>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart
          data={chartData}
          margin={{ top: 4, right: 4, left: -24, bottom: 0 }}
          onMouseMove={(state) => {
            if (state.isTooltipActive && typeof state.activeTooltipIndex === 'number') {
              setActiveIndex(state.activeTooltipIndex);
            }
          }}
          onMouseLeave={() => setActiveIndex(null)}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            dataKey="weekday"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            stroke="hsl(var(--border))"
          />
          <YAxis
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            stroke="hsl(var(--border))"
            allowDecimals={false}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={`hsl(var(--success) / ${0.4 + (entry.count / maxValue) * 0.6})`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      
      {/* Info bar below chart */}
      <div className="h-7 flex items-center justify-center rounded-[8px] bg-surface-muted border border-border/50">
        {activeIndex !== null && chartData[activeIndex] ? (
          <p className="text-xs text-foreground font-medium">
            {chartData[activeIndex].weekday_name}: {chartData[activeIndex].count} {pluralize(chartData[activeIndex].count, "выполнение", "выполнения", "выполнений")}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Всего за неделю: {totalCount} {pluralize(totalCount, "выполнение", "выполнения", "выполнений")}
          </p>
        )}
      </div>
    </div>
  );
}
