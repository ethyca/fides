import { theme } from "antd/lib";
import type { CSSProperties, RefObject } from "react";
import { useEffect, useMemo, useState } from "react";

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

export const deriveInterval = (
  data: { label: string }[],
): number => {
  if (data.length < 2) {
    return HOUR_MS;
  }
  const gap =
    new Date(data[1].label).getTime() -
    new Date(data[0].label).getTime();
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

export interface ChartDataRequest {
  interval: number;
  rangeMs: number;
}

export const pickIntervalHours = (
  rangeMs: number,
  containerWidth: number,
  minPointWidth: number,
): number => {
  const maxBuckets = Math.max(1, Math.floor(containerWidth / minPointWidth));
  const idealHours = Math.ceil(rangeMs / HOUR_MS / maxBuckets);
  return Math.max(1, Math.min(idealHours, 72));
};

export const computeDataRequest = (
  containerWidth: number,
  minPointWidth: number,
  timeRangeMs?: number,
): ChartDataRequest => {
  const maxBuckets = Math.max(1, Math.floor(containerWidth / minPointWidth));

  if (timeRangeMs != null) {
    const interval = pickIntervalHours(timeRangeMs, containerWidth, minPointWidth);
    return { interval, rangeMs: timeRangeMs };
  }

  const rangeMs = maxBuckets * HOUR_MS;
  return { interval: 1, rangeMs };
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
