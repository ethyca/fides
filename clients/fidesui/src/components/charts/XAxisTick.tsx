import { ChartText } from "./ChartText";
import { formatTimestamp } from "./chart-utils";

interface XAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  intervalMs: number;
  fill?: string;
}

export const XAxisTick = ({
  x,
  y,
  payload,
  intervalMs,
  fill,
}: XAxisTickProps) => (
  <ChartText x={Number(x)} y={Number(y) + 12} fill={fill}>
    {payload ? formatTimestamp(payload.value, intervalMs) : null}
  </ChartText>
);
