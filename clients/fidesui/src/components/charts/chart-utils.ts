import { theme } from "antd/lib";
import type { CSSProperties, RefObject } from "react";
import { useEffect, useMemo, useState } from "react";

import type { ChartInterval } from "./chart-constants";

export const HOUR_MS = 3_600_000;
export const DAY_MS = 86_400_000;

export const useContainerSize = (
  ref: RefObject<HTMLElement | null>,
): number => {
  const [size, setSize] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      const rect = entry.contentRect;
      setSize(Math.min(rect.width, rect.height));
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
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  // Hourly: time only
  if (intervalMs <= HOUR_MS) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  // Sub-daily (e.g. 6h): short date + time
  if (intervalMs < DAY_MS) {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  // Daily and above: date only
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

/**
 * Derives the time interval from the first two consecutive data points.
 * Assumes the data is sorted chronologically with uniform spacing.
 */
export const deriveInterval = (data: { timestamp: string }[]): number => {
  if (data.length < 2) {
    return HOUR_MS;
  }
  const gap =
    new Date(data[1].timestamp).getTime() -
    new Date(data[0].timestamp).getTime();
  return gap > 0 ? gap : HOUR_MS;
};

export const tooltipLabelFormatter = (
  label: string,
  intervalMs: number,
): string => {
  const date = new Date(label);
  if (Number.isNaN(date.getTime())) {
    return label;
  }
  // Hourly or sub-daily: full date + time
  if (intervalMs < DAY_MS) {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }
  // Daily+: full date
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export const useContainerWidth = (
  ref: RefObject<HTMLElement | null>,
): number => {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      setWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return width;
};

// export interface TimeSeriesConfig<T> {
//   points: T[];
//   timestampKey: keyof T & string;
//   valueKey: keyof T & string;
// }

// export interface BucketedResult {
//   data: { label: string; value: number }[];
//   interval: ChartInterval;
// }

const INTERVAL_MS: Record<ChartInterval, number> = {
  "1h": HOUR_MS,
  "6h": 6 * HOUR_MS,
  "1d": DAY_MS,
  "3d": 3 * DAY_MS,
};

const INTERVAL_ORDER: ChartInterval[] = ["1h", "6h", "1d", "3d"];

export const intervalToMs = (interval: ChartInterval): number =>
  INTERVAL_MS[interval];

export interface ChartDataRequest {
  interval: ChartInterval;
  rangeMs: number;
}

export const pickBucketInterval = (
  rangeMs: number,
  containerWidth: number,
  barWidth: number,
): ChartInterval => {
  const maxBuckets = Math.max(1, Math.floor(containerWidth / barWidth));

  return (
    INTERVAL_ORDER.find(
      (interval) => Math.ceil(rangeMs / INTERVAL_MS[interval]) <= maxBuckets,
    ) ?? "3d"
  );
};

export const computeDataRequest = (
  containerWidth: number,
  barWidth: number,
  timeRangeMs?: number,
): ChartDataRequest => {
  const maxBuckets = Math.max(1, Math.floor(containerWidth / barWidth));

  if (timeRangeMs != null) {
    const interval = pickBucketInterval(timeRangeMs, containerWidth, barWidth);
    return { interval, rangeMs: timeRangeMs };
  }

  // No range provided — fill the container at the finest interval
  const interval = INTERVAL_ORDER[0];
  const rangeMs = maxBuckets * INTERVAL_MS[interval];
  return { interval, rangeMs };
};

// export const bucketTimeSeries = <T>(
//   points: T[],
//   timestampKey: keyof T & string,
//   valueKey: keyof T & string,
//   interval: ChartInterval,
// ): BucketedResult => {
//   const ms = INTERVAL_MS[interval];
//
//   if (points.length === 0) {
//     return { data: [], interval };
//   }
//
//   const timestamps = points.map((p) =>
//     new Date(p[timestampKey] as string).getTime(),
//   );
//   const minTs = Math.min(...timestamps);
//   const maxTs = Math.max(...timestamps);
//   const range = maxTs - minTs;
//
//   if (range === 0) {
//     const total = points.reduce((sum, p) => sum + Number(p[valueKey]), 0);
//     return {
//       data: [{ label: new Date(minTs).toISOString(), value: total }],
//       interval,
//     };
//   }
//
//   const flooredStart = Math.floor(minTs / ms) * ms;
//   const bucketCount = Math.max(1, Math.ceil((maxTs - flooredStart) / ms));
//
//   const buckets = Array.from({ length: bucketCount }, (_, index) => ({
//     label: new Date(flooredStart + index * ms).toISOString(),
//     value: 0,
//   }));
//
//   timestamps.forEach((ts, idx) => {
//     const bucketIndex = Math.min(
//       Math.floor((ts - flooredStart) / ms),
//       bucketCount - 1,
//     );
//     buckets[bucketIndex].value += Number(points[idx][valueKey]);
//   });
//
//   return { data: buckets, interval };
// };

// export const useTimeSeriesBuckets = <T>(
//   config: TimeSeriesConfig<T> | undefined,
//   containerWidth: number,
//   barWidth: number,
// ): BucketedResult | null => {
//   return useMemo(() => {
//     if (!config || containerWidth <= 0 || config.points.length === 0) {
//       return null;
//     }
//
//     const { points, timestampKey, valueKey } = config;
//     const timestamps = points.map((p) =>
//       new Date(p[timestampKey] as string).getTime(),
//     );
//     const rangeMs = Math.max(...timestamps) - Math.min(...timestamps);
//     const interval = pickBucketInterval(rangeMs, containerWidth, barWidth);
//
//     return bucketTimeSeries(points, timestampKey, valueKey, interval);
//   }, [config, containerWidth, barWidth]);
// };

export const useTooltipContentStyle = (): CSSProperties => {
  const { token } = theme.useToken();
  return useMemo(
    () => ({
      backgroundColor: token.colorBgElevated,
      border: `1px solid ${token.colorBorder}`,
      borderRadius: token.borderRadiusLG,
      boxShadow: token.boxShadowSecondary,
    }),
    [
      token.colorBgElevated,
      token.colorBorder,
      token.borderRadiusLG,
      token.boxShadowSecondary,
    ],
  );
};
