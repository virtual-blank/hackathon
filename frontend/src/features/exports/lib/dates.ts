/**
 * Get today's date in YYYY-MM-DD format for the given timezone.
 * Uses Intl.DateTimeFormat to avoid local-UTC shifts.
 */
export function todayIso(timezone: string): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

/**
 * Shift an ISO date (YYYY-MM-DD) by a number of days.
 */
export function shiftDays(iso: string, delta: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const t = new Date(Date.UTC(y, m - 1, d + delta))
  return t.toISOString().slice(0, 10)
}

/**
 * Start of the current year in the given timezone.
 */
export function startOfYear(iso: string): string {
  return `${iso.slice(0, 4)}-01-01`
}

/**
 * Format YYYY-MM-DD to DD.MM.YYYY for display.
 */
export function formatDateDMY(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}.${m}.${y}`
}
