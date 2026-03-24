import { theme } from "antd/lib";
import { useEffect, useId, useRef } from "react";
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
  pickIntervalHours,
  useChartAnimation,
  useContainerSize,
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
  /** Total time span of the data in milliseconds. Used to compute the ideal interval. */
  rangeMs?: number;
  /** Called when the ideal fetch interval changes (e.g. on container resize). */
  onIntervalChange?: (intervalHours: number) => void;
  animationDuration?: number;
  showTooltip?: boolean;
  showGrid?: boolean;
}

export const AreaChart = ({
  data,
  series,
  rangeMs,
  onIntervalChange,
  animationDuration = CHART_ANIMATION.defaultDuration,
  showTooltip = true,
  showGrid = true,
}: AreaChartProps) => {
  const { token } = theme.useToken();
  const animationActive = useChartAnimation(animationDuration);
  const gradientPrefix = `area-gradient-${useId()}`;

  const containerRef = useRef<HTMLDivElement>(null);
  const { width: containerWidth } = useContainerSize(containerRef);

  const onIntervalChangeRef = useRef(onIntervalChange);
  useEffect(() => {
    onIntervalChangeRef.current = onIntervalChange;
  });

  const chartData = data ?? [];

  useEffect(() => {
    if (onIntervalChangeRef.current && rangeMs && rangeMs > 0 && containerWidth > 0) {
      onIntervalChangeRef.current(
        pickIntervalHours(rangeMs, containerWidth, MIN_PX_PER_POINT),
      );
    }
  }, [rangeMs, containerWidth]);

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
