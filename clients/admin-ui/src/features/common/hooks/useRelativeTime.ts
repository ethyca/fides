import { formatDistanceToNow } from "date-fns";
import { useEffect, useState } from "react";

const MINUTE_MS = 60_000;

/**
 * Returns a human-readable relative time string (e.g. "5 minutes ago") for
 * the given date, refreshing at the given interval. Returns an empty string
 * when date is null or undefined.
 */
export const useRelativeTime = (
  date: Date | null | undefined,
  intervalMs: number = MINUTE_MS,
): string => {
  const [relativeTime, setRelativeTime] = useState(() =>
    date ? formatDistanceToNow(date, { addSuffix: true }) : "",
  );

  useEffect(() => {
    if (!date) {
      setRelativeTime("");
      return undefined;
    }
    setRelativeTime(formatDistanceToNow(date, { addSuffix: true }));
    const interval = setInterval(() => {
      setRelativeTime(formatDistanceToNow(date, { addSuffix: true }));
    }, intervalMs);
    return () => {
      clearInterval(interval);
    };
  }, [date, intervalMs]);

  return relativeTime;
};
