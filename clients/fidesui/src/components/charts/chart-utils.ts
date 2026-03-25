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

/**
 * Build a smooth closed Catmull-Rom spline SVG path through `points`.
 * `alpha` controls curve tightness (0 = uniform, 0.5 = centripetal, 1 = chordal).
 */
export function catmullRomClosedPath(
  points: { x: number; y: number }[],
  alpha = 0.5,
): string {
  const n = points.length;
  if (n < 3) {
    return "";
  }

  const eps = 1e-6;
  const segments: string[] = [];
  for (let i = 0; i < n; i += 1) {
    const p0 = points[(i - 1 + n) % n];
    const p1 = points[i];
    const p2 = points[(i + 1) % n];
    const p3 = points[(i + 2) % n];

    const d1 = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    const d0 = Math.hypot(p1.x - p0.x, p1.y - p0.y);
    const d2 = Math.hypot(p3.x - p2.x, p3.y - p2.y);

    const a0 = Math.max(d0 ** alpha, eps);
    const a1 = Math.max(d1 ** alpha, eps);
    const a2 = Math.max(d2 ** alpha, eps);

    const cp1x =
      (a0 * a0 * p2.x -
        a1 * a1 * p0.x +
        (2 * a0 * a0 + 3 * a0 * a1 + a1 * a1) * p1.x) /
      (3 * a0 * (a0 + a1));
    const cp1y =
      (a0 * a0 * p2.y -
        a1 * a1 * p0.y +
        (2 * a0 * a0 + 3 * a0 * a1 + a1 * a1) * p1.y) /
      (3 * a0 * (a0 + a1));

    const cp2x =
      (a2 * a2 * p1.x -
        a1 * a1 * p3.x +
        (2 * a2 * a2 + 3 * a2 * a1 + a1 * a1) * p2.x) /
      (3 * a2 * (a2 + a1));
    const cp2y =
      (a2 * a2 * p1.y -
        a1 * a1 * p3.y +
        (2 * a2 * a2 + 3 * a2 * a1 + a1 * a1) * p2.y) /
      (3 * a2 * (a2 + a1));

    if (i === 0) {
      segments.push(`M${p1.x},${p1.y}`);
    }
    segments.push(`C${cp1x},${cp1y},${cp2x},${cp2y},${p2.x},${p2.y}`);
  }
  segments.push("Z");
  return segments.join(" ");
}

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
