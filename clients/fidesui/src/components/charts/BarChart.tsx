import { theme } from "antd/lib";
import { useEffect, useRef } from "react";
import {
  Bar,
  BarChart as RechartsBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import type { AntColorTokenKey, BarSize } from "./chart-constants";
import {
  BAR_SIZE_TOKEN,
  CHART_ANIMATION,
  LABEL_WIDTH,
} from "./chart-constants";
import {
  calcTickInterval,
  deriveInterval,
  formatTimestamp,
  pickIntervalHours,
  useChartAnimation,
  useContainerSize,
} from "./chart-utils";
import { XAxisTick } from "./XAxisTick";

export interface BarChartDataPoint {
  label: string;
  value: number;
}

export interface BarChartProps {
  data?: BarChartDataPoint[];
  color?: AntColorTokenKey;
  /** Total time span of the data in milliseconds. Used to compute the ideal interval. */
  rangeMs?: number;
  /** Called when the ideal fetch interval changes (e.g. on container resize). */
  onIntervalChange?: (intervalHours: number) => void;
  animationDuration?: number;
  showTooltip?: boolean;
  size?: BarSize;
}

export const BarChart = ({
  data,
  color = "colorText",
  rangeMs,
  onIntervalChange,
  animationDuration = CHART_ANIMATION.defaultDuration,
  showTooltip = true,
  size = "md",
}: BarChartProps) => {
  const { token } = theme.useToken();
  const animationActive = useChartAnimation(animationDuration);
  const fill = token[color];
  const barWidth = token[BAR_SIZE_TOKEN[size]];

  const containerRef = useRef<HTMLDivElement>(null);
  const { width: containerWidth } = useContainerSize(containerRef);

  const chartData = data ?? [];

  useEffect(() => {
    if (onIntervalChange && rangeMs && rangeMs > 0 && containerWidth > 0) {
      onIntervalChange(
        pickIntervalHours(rangeMs, containerWidth, barWidth),
      );
    }
  }, [onIntervalChange, rangeMs, containerWidth, barWidth]);

  const intervalMs = deriveInterval(chartData);
  const tickInterval = calcTickInterval(
    chartData.length,
    containerWidth,
    LABEL_WIDTH,
  );

  return (
    <div ref={containerRef} className="h-full w-full">
      {containerWidth > 0 && (
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart
            data={chartData}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            barCategoryGap="8%"
          >
            <XAxis
              dataKey="label"
              tick={
                <XAxisTick
                  intervalMs={intervalMs}
                  fill={token.colorTextTertiary}
                />
              }
              interval={tickInterval}
              axisLine={false}
              tickLine={false}
            />
            {showTooltip && (
              <Tooltip
                cursor={false}
                contentStyle={{
                  backgroundColor: token.colorBgElevated,
                  border: `1px solid ${token.colorBorder}`,
                  borderRadius: token.borderRadiusLG,
                  boxShadow: token.boxShadowSecondary,
                }}
                labelFormatter={(label) =>
                  formatTimestamp(String(label), intervalMs, true)
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
            />
          </RechartsBarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
