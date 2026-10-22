import type { DailyActivityPointSchema } from "@/api/generated/model";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format, parseISO } from "date-fns";
import { ru } from "date-fns/locale";

type DailyActivityChartProps = {
  data: DailyActivityPointSchema[];
};

export function DailyActivityChart({ data }: DailyActivityChartProps) {
  const chartData = data.map((point) => ({
    date: point.date,
    count: point.completed_count,
  }));

  return (
    <div className="col-span-1 md:col-span-2 rounded-[16px] bg-surface border border-border p-4 space-y-3">
      <h4 className="font-display text-base font-medium">Ежедневная активность</h4>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id="activityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
              <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            dataKey="date"
            tickFormatter={(value) => format(parseISO(value), "d MMM", { locale: ru })}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            stroke="hsl(var(--border))"
          />
          <YAxis
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            stroke="hsl(var(--border))"
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--surface))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "13px",
            }}
            labelFormatter={(value) => format(parseISO(value as string), "d MMMM", { locale: ru })}
            formatter={(value) => {
              const count = typeof value === 'number' ? value : 0;
              return [`${count} привычек`, "Выполнено"];
            }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="hsl(var(--success))"
            strokeWidth={2}
            fill="url(#activityGradient)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
