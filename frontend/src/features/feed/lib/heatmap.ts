import { parseISO, startOfDay, eachDayOfInterval, format, isToday } from 'date-fns'

export type HeatmapDay = {
  date: string
  isCompleted: boolean
  isBeforeStart: boolean
  isToday: boolean
}

export type HeatmapWeek = HeatmapDay[]

export function buildHeatmapData(
  logs: Array<{ completed_date: string }>,
  startDate: string,
  weeksCount = 16
): HeatmapWeek[] {
  const today = startOfDay(new Date())
  const startDateObj = startOfDay(parseISO(startDate))
  
  // Build a date range for the last N weeks ending today
  const endDate = today
  const daysCount = weeksCount * 7
  const firstDay = new Date(endDate)
  firstDay.setDate(firstDay.getDate() - daysCount + 1)
  
  const allDays = eachDayOfInterval({ start: firstDay, end: endDate })
  
  // Create a set of completed dates for fast lookup
  const completedDates = new Set(logs.map((log) => log.completed_date))
  
  // Map days to HeatmapDay
  const heatmapDays: HeatmapDay[] = allDays.map((day) => {
    const dateStr = format(day, 'yyyy-MM-dd')
    return {
      date: dateStr,
      isCompleted: completedDates.has(dateStr),
      isBeforeStart: day < startDateObj,
      isToday: isToday(day),
    }
  })
  
  // Group into weeks (7 days each)
  const weeks: HeatmapWeek[] = []
  for (let i = 0; i < heatmapDays.length; i += 7) {
    weeks.push(heatmapDays.slice(i, i + 7))
  }
  
  return weeks
}

