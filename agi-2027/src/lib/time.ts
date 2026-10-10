const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/**
 * Short countdown text: "2d 4h", "4h 12m", "12m 05s". Rounds down, so a
 * countdown never claims more time than is left.
 */
export function formatCountdown(ms: number): string {
  if (ms <= 0) return "0s";
  const days = Math.floor(ms / DAY);
  const hours = Math.floor((ms % DAY) / HOUR);
  const minutes = Math.floor((ms % HOUR) / MINUTE);
  const seconds = Math.floor((ms % MINUTE) / 1000);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
}

/*
 * Dates are assembled from Intl parts instead of Intl's own pattern: Node and
 * browsers ship different ICU versions that punctuate the same pattern
 * differently ("Tue 12 Jan" vs "Tue, 12 Jan"), which breaks hydration.
 */
const formatters = new Map<string, Intl.DateTimeFormat>();

function dateParts(date: Date | string, timeZone?: string) {
  const key = timeZone ?? "local";
  let formatter = formatters.get(key);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
      timeZone,
    });
    formatters.set(key, formatter);
  }
  const parts: Record<string, string> = {};
  for (const part of formatter.formatToParts(new Date(date))) parts[part.type] = part.value;
  return parts;
}

/** "Tue 12 Jan, 17:00" in a given time zone (defaults to the viewer's). */
export function formatDateTime(date: Date | string, timeZone?: string): string {
  const p = dateParts(date, timeZone);
  return `${p.weekday} ${p.day} ${p.month}, ${p.hour}:${p.minute}`;
}

/** "17:00 UTC", the UTC half of "local time plus UTC". */
export function formatUtcTime(date: Date | string): string {
  const p = dateParts(date, "UTC");
  return `${p.hour}:${p.minute} UTC`;
}
