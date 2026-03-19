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
  if (intervalMs < DAY_MS) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
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
