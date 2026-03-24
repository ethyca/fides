import { theme } from "antd/lib";
import { useMemo, useRef } from "react";
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
  HOUR_MS,
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
  animationDuration?: number;
  showTooltip?: boolean;
  size?: BarSize;
}

export const BarChart = ({
  data,
  color = "colorText",
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

  const rawData = data ?? [];

  const chartData = useMemo(() => {
    if (containerWidth <= 0 || rawData.length < 2) {
      return rawData;
    }

    const timestamps = rawData.map((d) => new Date(d.label).getTime());
    const minTs = timestamps.reduce((a, b) => Math.min(a, b), Infinity);
    const maxTs = timestamps.reduce((a, b) => Math.max(a, b), -Infinity);
    const rangeMs = maxTs - minTs;
    if (rangeMs <= 0) {
      return rawData;
    }

    const intervalMs =
      pickIntervalHours(rangeMs, containerWidth, barWidth) * HOUR_MS;
    const flooredStart = Math.floor(minTs / intervalMs) * intervalMs;
    const bucketCount = Math.max(
      1,
      Math.ceil((maxTs - flooredStart) / intervalMs),
    );

    const buckets: BarChartDataPoint[] = Array.from(
      { length: bucketCount },
      (_, i) => ({
        label: new Date(flooredStart + i * intervalMs).toISOString(),
        value: 0,
      }),
    );

    timestamps.forEach((ts, idx) => {
      const bucketIndex = Math.min(
        Math.floor((ts - flooredStart) / intervalMs),
        bucketCount - 1,
      );
      buckets[bucketIndex].value += rawData[idx].value;
    });

    return buckets;
  }, [rawData, containerWidth, barWidth]);

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
