import { formatDistanceToNow } from "date-fns";
import { useEffect, useState } from "react";

const MINUTE_S = 60;

/**
 * Returns a human-readable relative time string (e.g. "5 minutes ago") for
 * the given date, refreshing at the given interval. Returns an empty string
 * when date is null or undefined.
 */
export const useRelativeTime = (
  date: Date | null | undefined,
  intervalSeconds: number = MINUTE_S,
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
    }, intervalSeconds * 1000);
    return () => {
      clearInterval(interval);
    };
  }, [date, intervalSeconds]);

  return relativeTime;
};
