import { theme } from "antd/lib";
import type { CSSProperties, RefObject } from "react";
import { useEffect, useMemo, useState } from "react";

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
  const [active, setActive] = useState(true);
  useEffect(() => {
    if (animationDuration <= 0) {
      setActive(false);
      return undefined;
    }
    const id = setTimeout(() => setActive(false), animationDuration);
    return () => clearTimeout(id);
  }, [animationDuration]);
  return active;
};

/**
 * Format a timestamp for display on chart axes or tooltips.
 * When `verbose` is true (tooltips), includes more context like year or AM/PM.
 */
export const formatTimestamp = (
  timestamp: string,
  intervalMs: number,
  verbose = false,
): string => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  if (verbose) {
    if (intervalMs < DAY_MS) {
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    }
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
  if (intervalMs <= HOUR_MS) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  if (intervalMs < DAY_MS) {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
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
  return Math.max(1, Math.min(idealHours, 72));
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
