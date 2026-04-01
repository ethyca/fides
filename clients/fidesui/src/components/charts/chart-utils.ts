import { format, isValid } from "date-fns";
import type { RefObject } from "react";
import { useEffect, useState } from "react";

import { MAX_INTERVAL_HOURS } from "./chart-constants";

export const HOUR_MS = 3_600_000;
export const DAY_MS = 86_400_000;

export interface ContainerSize {
  width: number;
  height: number;
}

export const useContainerSize = (
  ref: RefObject<HTMLElement | null>,
): ContainerSize => {
  const [size, setSize] = useState<ContainerSize>({ width: 0, height: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      const rect = entry.contentRect;
      setSize({ width: rect.width, height: rect.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return size;
};

export const useChartAnimation = (animationDuration: number): boolean => {
  const [animationActive, setAnimationActive] = useState(true);
  useEffect(() => {
    if (animationDuration <= 0) {
      return undefined;
    }
    const startTime = performance.now();
    let animationId: number;
    const tick = (now: number) => {
      if (now - startTime >= animationDuration) {
        setAnimationActive(false);
      } else {
        animationId = requestAnimationFrame(tick);
      }
    };
    animationId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationId);
  }, [animationDuration]);
  return animationActive;
};

/** Format a timestamp for chart axes (verbose=false) or tooltips (verbose=true). */
export const formatTimestamp = (
  timestamp: string,
  intervalMs: number,
  verbose = false,
): string => {
  const date = new Date(timestamp);
  if (!isValid(date)) {
    return timestamp;
  }
  if (intervalMs >= DAY_MS) {
    return format(date, verbose ? "MMM d, yyyy" : "MMM d");
  }
  if (intervalMs > HOUR_MS) {
    return format(date, verbose ? "MMM d, HH:mm" : "MMM d, HH:mm");
  }
  return format(date, verbose ? "MMM d, HH:mm" : "HH:mm");
};

/** Infer the interval between data points from the first two labels. */
export const deriveInterval = (data: { label: string }[]): number => {
  if (data.length < 2) {
    return HOUR_MS;
  }
  const gap =
    new Date(data[1].label).getTime() - new Date(data[0].label).getTime();
  return gap > 0 ? gap : HOUR_MS;
};

/** Pick a bucket size (in hours) that fits the data range into the container. */
export const pickIntervalHours = (
  rangeMs: number,
  containerWidth: number,
  minPointWidth: number,
): number => {
  const maxBuckets = Math.max(1, Math.floor(containerWidth / minPointWidth));
  const idealHours = Math.ceil(rangeMs / HOUR_MS / maxBuckets);
  return Math.max(1, Math.min(idealHours, MAX_INTERVAL_HOURS));
};

/** Calculate how many ticks to skip so labels don't overlap. */
export const calcTickInterval = (
  pointCount: number,
  containerWidth: number,
  labelWidth: number,
): number => {
  const slotWidth =
    pointCount > 0 && containerWidth > 0
      ? containerWidth / pointCount
      : labelWidth;
  return Math.max(0, Math.ceil(labelWidth / slotWidth) - 1);
};
