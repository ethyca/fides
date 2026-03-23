import { theme } from "antd/lib";
import { useId, useMemo, useRef } from "react";
import {
  Area,
  AreaChart as RechartsAreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import {
  CHART_ANIMATION,
  CHART_STROKE,
  LABEL_WIDTH,
  MIN_PX_PER_POINT,
} from "./chart-constants";
import {
  calcTickInterval,
  deriveInterval,
  formatTimestamp,
  HOUR_MS,
  pickIntervalHours,
  useChartAnimation,
  useContainerSize,
  useTooltipContentStyle,
} from "./chart-utils";
import { ChartGradient } from "./ChartGradient";
import { XAxisTick } from "./XAxisTick";

export interface AreaChartSeries {
  key: string;
  name: string;
  color?: AntColorTokenKey;
}

export interface AreaChartDataPoint {
  label: string;
  [key: string]: string | number;
}

export interface AreaChartProps {
  data?: AreaChartDataPoint[];
  series: AreaChartSeries[];
  animationDuration?: number;
  showTooltip?: boolean;
  showGrid?: boolean;
}

export const AreaChart = ({
  data,
  series,
  animationDuration = CHART_ANIMATION.defaultDuration,
  showTooltip = true,
  showGrid = true,
}: AreaChartProps) => {
  const { token } = theme.useToken();
  const tooltipContentStyle = useTooltipContentStyle();
  const animationActive = useChartAnimation(animationDuration);
  const gradientPrefix = `area-gradient-${useId()}`;

  const containerRef = useRef<HTMLDivElement>(null);
  const { width: containerWidth } = useContainerSize(containerRef);

  const rawData = data ?? [];
  const seriesKeys = useMemo(() => series.map((s) => s.key), [series]);

  const chartData = useMemo(() => {
    if (containerWidth <= 0 || rawData.length < 2) {
      return rawData;
    }

    const timestamps = rawData.map((point) => new Date(point.label).getTime());
    const minTs = timestamps.reduce((a, b) => Math.min(a, b), Infinity);
    const maxTs = timestamps.reduce((a, b) => Math.max(a, b), -Infinity);
    const rangeMs = maxTs - minTs;
    if (rangeMs <= 0) {
      return rawData;
    }

    const intervalMs =
      pickIntervalHours(rangeMs, containerWidth, MIN_PX_PER_POINT) * HOUR_MS;
    const flooredStart = Math.floor(minTs / intervalMs) * intervalMs;
    const bucketCount = Math.max(
      1,
      Math.ceil((maxTs - flooredStart) / intervalMs),
    );

    const buckets: AreaChartDataPoint[] = Array.from(
      { length: bucketCount },
      (_, index) => {
        const point: AreaChartDataPoint = {
          label: new Date(flooredStart + index * intervalMs).toISOString(),
        };
        seriesKeys.forEach((key) => {
          point[key] = 0;
        });
        return point;
      },
    );

    timestamps.forEach((ts, idx) => {
      const bucketIndex = Math.min(
        Math.floor((ts - flooredStart) / intervalMs),
        bucketCount - 1,
      );
      seriesKeys.forEach((key) => {
        (buckets[bucketIndex][key] as number) += Number(rawData[idx][key] ?? 0);
      });
    });

    return buckets;
  }, [rawData, seriesKeys, containerWidth]);

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
          <RechartsAreaChart
            data={chartData}
            margin={{ top: 5, right: 5, bottom: 0, left: -15 }}
          >
            {series.map((entry, index) => (
              <ChartGradient
                key={entry.key}
                id={`${gradientPrefix}-${index}`}
                color={token[entry.color ?? "colorText"]}
              />
            ))}
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={token.colorBorderSecondary}
                vertical={false}
              />
            )}
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
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{
                fontSize: token.fontSizeSM,
                fill: token.colorTextTertiary,
              }}
            />
            {showTooltip && (
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelFormatter={(label) =>
                  formatTimestamp(String(label), intervalMs, true)
                }
              />
            )}
            {series.map((entry, index) => (
              <Area
                key={entry.key}
                type="monotone"
                dataKey={entry.key}
                name={entry.name}
                stroke={token[entry.color ?? "colorText"]}
                strokeWidth={CHART_STROKE.strokeWidth}
                strokeOpacity={CHART_STROKE.strokeOpacity}
                strokeLinecap={CHART_STROKE.strokeLinecap}
                strokeLinejoin={CHART_STROKE.strokeLinejoin}
                fill={`url(#${gradientPrefix}-${index})`}
                dot={false}
                activeDot={{ r: CHART_STROKE.dotRadius }}
                isAnimationActive={animationActive}
                animationDuration={animationDuration}
                animationEasing={CHART_ANIMATION.easing}
              />
            ))}
          </RechartsAreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
