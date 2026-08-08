const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** Notification-style relative time. Falls back to empty string on bad input. */
export function relativeTime(raw: string | null): string {
  if (!raw) return "";

  const then = new Date(raw).getTime();
  if (isNaN(then)) return "";

  const delta = Date.now() - then;
  if (delta < HOUR) return `${Math.max(1, Math.round(delta / MINUTE))}m ago`;
  if (delta < DAY) return `${Math.round(delta / HOUR)}h ago`;
  if (delta < 7 * DAY) return `${Math.round(delta / DAY)}d ago`;

  return new Date(then).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function sequence(n: number): string {
  return `No. ${String(n).padStart(3, "0")}`;
}