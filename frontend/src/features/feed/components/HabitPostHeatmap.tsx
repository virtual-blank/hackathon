import { useMemo } from 'react'
import {
  format,
  parseISO,
  startOfDay,
  differenceInCalendarDays,
  subDays,
  getDay,
} from 'date-fns'
import { ru } from 'date-fns/locale'
import { Flame } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'
import { buildHeatmapData } from '../lib/heatmap'
import { cn } from '@/shared/lib/utils'
import { pluralizeDays } from '@/shared/lib/date'
import type {
  HabitFeedLogOutputSchema,
  HabitOutputSchema,
} from '@/api/generated/model'

type HabitPostHeatmapProps = {
  habit: HabitOutputSchema
  habitLogs: HabitFeedLogOutputSchema[]
  totalLogsCount: number
}

export function HabitPostHeatmap({
  habit,
  habitLogs,
  totalLogsCount,
}: HabitPostHeatmapProps) {
  const weeks = useMemo(
    () => buildHeatmapData(habitLogs, habit.start_date, 16),
    [habitLogs, habit.start_date]
  )

  // Month labels
  const monthLabels = useMemo(() => {
    const labels: Array<{ week: number; label: string }> = []
    let lastMonth = -1

    weeks.forEach((week, weekIdx) => {
      if (week.length === 0) return
      const firstDayOfWeek = parseISO(week[0].date)
      const monthNum = firstDayOfWeek.getMonth()

      if (monthNum !== lastMonth) {
        labels.push({
          week: weekIdx,
          label: format(firstDayOfWeek, 'MMM', { locale: ru }),
        })
        lastMonth = monthNum
      }
    })

    return labels
  }, [weeks])

  // Analytics calculations
  const analytics = useMemo(() => {
    // Stability
    const firstLogDate =
      habitLogs.length > 0 ? parseISO(habitLogs[0].completed_date) : parseISO(habit.start_date)
    const earliestDate =
      firstLogDate < parseISO(habit.start_date) ? firstLogDate : parseISO(habit.start_date)
    const today = startOfDay(new Date())
    const totalDays = Math.max(1, differenceInCalendarDays(today, earliestDate) + 1)
    const stability = Math.min(100, Math.round((totalLogsCount / totalDays) * 100))

    // Last 30 days
    const last30Days = subDays(new Date(), 30)
    const last30DaysCount = habitLogs.filter(
      (log) => parseISO(log.completed_date) >= last30Days
    ).length

    // Best weekday
    const weekdayCounts: Record<number, number> = {}
    habitLogs.forEach((log) => {
      const day = getDay(parseISO(log.completed_date))
      weekdayCounts[day] = (weekdayCounts[day] || 0) + 1
    })
    const bestWeekdayNum = Object.entries(weekdayCounts).sort(
      (a, b) => Number(b[1]) - Number(a[1])
    )[0]?.[0]
    const bestWeekday =
      bestWeekdayNum !== undefined
        ? ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'][parseInt(bestWeekdayNum)]
        : '—'

    return {
      stability,
      totalDays,
      last30DaysCount,
      bestWeekday,
    }
  }, [habitLogs, habit.start_date, totalLogsCount])

  return (
    <div className="rounded-[14px] bg-surface-muted/70 border border-border/60 p-4 md:px-6 md:py-5 flex flex-col md:flex-row items-center gap-6 md:gap-8">
      {/* Left: Heatmap with axis labels */}
      <div className="shrink-0 space-y-2 overflow-x-auto">
          {/* Month labels */}
          <div className="flex relative" style={{ height: '16px', marginLeft: '22px' }}>
            {monthLabels.map(({ week, label }) => (
              <div
                key={week}
                className="absolute text-[10px] text-muted-foreground"
                style={{ left: `${week * 14}px` }}
              >
                {label}
              </div>
            ))}
          </div>

          {/* Grid with day labels */}
          <div className="flex gap-[2px]">
            {/* Day labels */}
            <div className="flex flex-col gap-[2px] mr-1">
              {['Пн', '', 'Ср', '', 'Пт', '', 'Вс'].map((day, idx) => (
                <div
                  key={idx}
                  className="text-[10px] leading-none text-muted-foreground flex items-center"
                  style={{ height: '12px' }}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Week columns */}
            <TooltipProvider delayDuration={100}>
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col gap-[2px]">
                  {week.map((day, dayIndex) => {
                    const dayDate = parseISO(day.date)
                    const tooltipText = format(dayDate, 'd MMM, yyyy', { locale: ru })

                    return (
                      <Tooltip key={dayIndex}>
                        <TooltipTrigger asChild>
                          <div
                            className={cn(
                              'w-3 h-3 rounded-[3px] transition-all',
                              day.isBeforeStart && 'opacity-30 bg-muted',
                              !day.isBeforeStart && !day.isCompleted && 'bg-heat-0',
                              !day.isBeforeStart && day.isCompleted && 'shadow-sm'
                            )}
                            style={
                              !day.isBeforeStart && day.isCompleted
                                ? {
                                    backgroundColor: habit.color_hex,
                                    boxShadow: `0 0 6px ${habit.color_hex}40`,
                                  }
                                : undefined
                            }
                          />
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs">
                          <p>
                            {tooltipText}
                            {day.isCompleted ? ' — выполнено' : ' — не выполнено'}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    )
                  })}
                </div>
              ))}
            </TooltipProvider>
          </div>
      </div>

      {/* Right: Three metrics in a fixed grid (always 3 columns) */}
      <div className="flex-1 w-full grid grid-cols-3 items-center justify-items-center gap-4">
        {/* Column 1: Current streak + Record */}
        <div className="flex flex-col items-center justify-center text-center">
          {/* Row 1: Number + Flame */}
          <div className="flex items-center justify-center gap-1 leading-none">
            <div className="font-display text-[32px] md:text-[36px] font-medium tabular-nums text-foreground leading-none">
              {habit.current_streak_days}
            </div>
            {habit.current_streak_days > 0 &&
              habit.current_streak_days === habit.max_streak_days && (
                <Flame className="w-7 h-7 text-streak shrink-0" strokeWidth={1.75} />
              )}
          </div>

          {/* Row 2: Word "день/дня/дней" */}
          <div className="font-display text-[20px] md:text-[22px] font-medium text-foreground leading-tight mt-0.5">
            {pluralizeDays(habit.current_streak_days)}
          </div>

          {/* Row 3: Record label */}
          <div className="text-xs text-muted-foreground mt-1 whitespace-nowrap">
            Рекорд: {habit.max_streak_days} дн.
          </div>
        </div>

        {/* Column 2: Last 30 days + Best weekday */}
        <div className="flex flex-col items-center justify-center text-center">
          <div className="font-display text-[26px] md:text-[30px] font-medium tabular-nums text-foreground leading-tight whitespace-nowrap">
            {analytics.last30DaysCount} отм.
          </div>
          <div className="text-xs text-muted-foreground mt-1.5 whitespace-nowrap">
            Чаще всего: {analytics.bestWeekday}
          </div>
        </div>

        {/* Column 3: Stability % + Progress bar + Days */}
        <div className="flex flex-col items-center justify-center text-center w-full max-w-[130px]">
          <div className="font-display text-[26px] md:text-[30px] font-medium tabular-nums text-foreground leading-tight">
            {analytics.stability}%
          </div>
          <div className="w-full h-1.5 rounded-full bg-border/60 overflow-hidden my-1.5">
            <div
              className="h-full rounded-full"
              style={{
                width: `${analytics.stability}%`,
                backgroundColor: habit.color_hex,
              }}
            />
          </div>
          <div className="text-xs text-muted-foreground whitespace-nowrap tabular-nums">
            {totalLogsCount} из {analytics.totalDays} дн.
          </div>
        </div>
      </div>
    </div>
  )
}
