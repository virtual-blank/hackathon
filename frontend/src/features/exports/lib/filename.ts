/**
 * Replace problematic filename characters and limit length.
 */
export function safeName(title: string): string {
  return title
    .replace(/[/\\:*?"<>|\s]+/g, '-')
    .slice(0, 40)
}
