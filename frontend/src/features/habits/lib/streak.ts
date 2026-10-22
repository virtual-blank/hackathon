const STREAK_SCALE_FLOOR = 7;

/**
 * Calculate streak heat value (0..1) for flame color gradient
 * Uses sqrt to make the gradient less steep
 */
export function getStreakHeat(streak: number, maxStreak: number): number {
  const effectiveMax = Math.max(maxStreak, STREAK_SCALE_FLOOR);
  const normalized = streak / effectiveMax;
  return Math.sqrt(normalized);
}

/**
 * Get flame color CSS string based on heat value (0..1)
 * 0..0.5: low -> mid (yellow to orange)
 * 0.5..1: mid -> high (orange to red)
 */
export function getFlameColor(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  
  if (clamped < 0.5) {
    const localT = clamped * 2;
    const percent = Math.round(localT * 100);
    return `color-mix(in oklab, var(--flame-mid) ${percent}%, var(--flame-low))`;
  } else {
    const localT = (clamped - 0.5) * 2;
    const percent = Math.round(localT * 100);
    return `color-mix(in oklab, var(--flame-high) ${percent}%, var(--flame-mid))`;
  }
}
