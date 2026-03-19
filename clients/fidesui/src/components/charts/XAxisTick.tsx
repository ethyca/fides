import { formatTimestamp } from "./chart-utils";
import { ChartText } from "./ChartText";

interface XAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  intervalMs: number;
  fill?: string;
}

export const XAxisTick = ({
  x = 0,
  y = 0,
  payload,
  intervalMs,
  fill,
}: XAxisTickProps) => (
  <ChartText x={x} y={y + 12} fill={fill}>
    {payload ? formatTimestamp(payload.value, intervalMs) : null}
  </ChartText>
);
