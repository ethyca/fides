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
  useChartAnimation,
  useTooltipContentStyle,
} from "./chart-utils";
import { ChartText } from "./ChartText";

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
  showTooltip?: boolean;
}

export const BarChart = ({
  data,
  color = "colorText",
  intervalMs,
  animationDuration = CHART_ANIMATION.defaultDuration,
  tickFormatter,
  showTooltip = true,
}: BarChartProps) => {
  const { token } = theme.useToken();
  const tooltipContentStyle = useTooltipContentStyle();
  const animationActive = useChartAnimation(animationDuration);
  const fill = token[color];

  const formatLabel =
    tickFormatter ??
    (intervalMs != null
      ? (label: string) => formatTimestamp(label, intervalMs)
      : undefined);

  const renderTick = ({
    x,
    y,
    payload,
  }: {
    x?: string | number;
    y?: string | number;
    payload?: { value: string };
  }) => (
    <ChartText
      x={Number(x ?? 0)}
      y={Number(y ?? 0) + 12}
      fill={token.colorTextTertiary}
    >
      {payload ? (formatLabel?.(payload.value) ?? payload.value) : null}
    </ChartText>
  );

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsBarChart
        data={data}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        barCategoryGap="8%"
      >
        <XAxis
          dataKey="label"
          tick={renderTick}
          axisLine={false}
          tickLine={false}
        />
        {showTooltip && (
          <Tooltip
            cursor={false}
            contentStyle={tooltipContentStyle}
            labelFormatter={
              intervalMs != null
                ? (label) => tooltipLabelFormatter(String(label), intervalMs)
                : undefined
            }
          />
        )}
        <Bar
          dataKey="value"
          fill={fill}
          radius={[1, 1, 0, 0]}
          isAnimationActive={animationActive}
          animationDuration={animationDuration}
          animationEasing={CHART_ANIMATION.easing}
          maxBarSize={CHART_STROKE.strokeWidth * 8}
        />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
};
