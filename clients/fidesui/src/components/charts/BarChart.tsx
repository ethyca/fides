import { theme } from "antd/lib";
import {
  Bar,
  BarChart as RechartsBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, CHART_STROKE } from "./chart-constants";
import {
  formatTimestamp,
  tooltipLabelFormatter,
  useTooltipContentStyle,
} from "./chart-utils";
import { XAxisTick } from "./XAxisTick";

export interface BarChartDataPoint {
  label: string;
  value: number;
}

export interface BarChartProps {
  data: BarChartDataPoint[];
  color?: AntColorTokenKey;
  intervalMs?: number;
  animationDuration?: number;
  tickFormatter?: (label: string) => string;
}

export const BarChart = ({
  data,
  color = "colorText",
  intervalMs,
  animationDuration = CHART_ANIMATION.defaultDuration,
  tickFormatter,
}: BarChartProps) => {
  const { token } = theme.useToken();
  const tooltipContentStyle = useTooltipContentStyle();
  const fill = token[color];

  const resolvedTickFormatter =
    tickFormatter ??
    (intervalMs != null
      ? (label: string) => formatTimestamp(label, intervalMs)
      : undefined);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsBarChart
        data={data}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        barCategoryGap="8%"
      >
        <XAxis
          dataKey="label"
          tickFormatter={resolvedTickFormatter}
          tick={
            intervalMs != null ? (
              <XAxisTick
                intervalMs={intervalMs}
                fill={token.colorTextTertiary}
              />
            ) : undefined
          }
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={false}
          contentStyle={tooltipContentStyle}
          labelFormatter={
            intervalMs != null
              ? (label) => tooltipLabelFormatter(String(label), intervalMs)
              : undefined
          }
        />
        <Bar
          dataKey="value"
          fill={fill}
          radius={[1, 1, 0, 0]}
          isAnimationActive={animationDuration > 0}
          animationDuration={animationDuration}
          animationEasing={CHART_ANIMATION.easing}
          maxBarSize={CHART_STROKE.strokeWidth * 8}
        />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
};
