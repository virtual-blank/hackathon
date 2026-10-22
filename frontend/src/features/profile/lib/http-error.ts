export function getHttpStatus(err: unknown): number | null {
  const m = /^HTTP (\d+)/.exec(err instanceof Error ? err.message : '')
  return m ? Number(m[1]) : null
}
