import { ChartText } from "fidesui";

import type { DataConsumerRequestPoint } from "./types";

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

export const deriveInterval = (data: DataConsumerRequestPoint[]): number => {
  if (data.length < 2) {
    return HOUR_MS;
  }
  return (
    new Date(data[1].timestamp).getTime() -
    new Date(data[0].timestamp).getTime()
  );
};

interface XAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  intervalMs: number;
  fill?: string;
}

export const XAxisTick = ({ x, y, payload, intervalMs, fill }: XAxisTickProps) => (
  <ChartText x={Number(x)} y={Number(y) + 12} fill={fill}>
    {payload ? formatTimestamp(payload.value, intervalMs) : null}
  </ChartText>
);
