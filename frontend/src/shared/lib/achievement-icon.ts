/**
 * Resolves achievement icon URL.
 * If URL is already absolute (starts with http/https), returns it as-is.
 * Otherwise, attempts to resolve as local asset path.
 */
export function resolveAchievementIcon(iconUrl: string): string {
  // If it's already a full URL, return as-is
  if (iconUrl.startsWith('http://') || iconUrl.startsWith('https://')) {
    return iconUrl;
  }

  // Try to resolve as local asset
  try {
    const match = iconUrl.match(/\/(\w+)-(\d+)/);
    if (match) {
      const [, category, threshold] = match;
      return `/src/assets/achievements/${category}-${threshold}.webp`;
    }
  } catch {
    // Ignore errors
  }
  
  return iconUrl || "";
}
