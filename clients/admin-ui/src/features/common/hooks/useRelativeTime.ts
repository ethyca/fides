import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { useEffect, useState } from "react";

dayjs.extend(relativeTime);

const MINUTE_S = 60;

const getRelativeTime = (date: Date) => dayjs(date).fromNow();

/**
 * Returns a human-readable relative time string (e.g. "5 minutes ago") for
 * the given date, refreshing at the given interval. Returns an empty string
 * when date is null or undefined.
 */
export const useRelativeTime = (
  date: Date | null | undefined,
  intervalSeconds: number = MINUTE_S,
): string => {
  const [timeAgo, setTimeAgo] = useState(() =>
    date ? getRelativeTime(date) : "",
  );

  useEffect(() => {
    if (!date) {
      setTimeAgo("");
      return undefined;
    }
    setTimeAgo(getRelativeTime(date));
    const interval = setInterval(() => {
      setTimeAgo(getRelativeTime(date));
    }, intervalSeconds * 1000);
    return () => {
      clearInterval(interval);
    };
  }, [date, intervalSeconds]);

  return timeAgo;
};
