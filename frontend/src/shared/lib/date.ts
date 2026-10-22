import { parseISO } from "date-fns";

export function formatFullDate(date: Date | string, timezone?: string): string {
  // Parse string dates (YYYY-MM-DD) to avoid UTC midnight shift
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  
  const options: Intl.DateTimeFormatOptions = {
    weekday: "long",
    day: "numeric",
    month: "short",
    timeZone: timezone || "UTC",
  };
  
  const formatted = new Intl.DateTimeFormat("ru-RU", options).format(dateObj);
  // Capitalize first letter
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export function pluralizeDays(count: number): string {
  const rules = new Intl.PluralRules("ru");
  const category = rules.select(count);
  
  const forms: Record<string, string> = {
    one: "день",
    few: "дня",
    many: "дней",
    other: "дней",
  };
  
  return forms[category] || forms.other;
}
