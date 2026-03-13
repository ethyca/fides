const HOUR_MS = 3_600_000;
const DAY_MS = 86_400_000;

export const pickInterval = (startMs: number, endMs: number): number => {
  const rangeMs = endMs - startMs;
  if (rangeMs <= DAY_MS) {
    return HOUR_MS;
  }
  if (rangeMs <= 7 * DAY_MS) {
    return 6 * HOUR_MS;
  }
  return DAY_MS;
};

export const formatTimestamp = (
  timestamp: string,
  intervalMs: number,
): string => {
  const date = new Date(timestamp);
  if (intervalMs < DAY_MS) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};
