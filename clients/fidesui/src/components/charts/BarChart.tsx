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
import type { ChartDataRequest } from "./chart-utils";
import {
  computeDataRequest,
  deriveInterval,
  tooltipLabelFormatter,
  useChartAnimation,
  useContainerSize,
  useTooltipContentStyle,
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
  onIntervalChange?: (request: ChartDataRequest) => void;
}

export const BarChart = ({
  data,
  color = "colorText",
  animationDuration = CHART_ANIMATION.defaultDuration,
  showTooltip = true,
  size = "md",
  onIntervalChange,
}: BarChartProps) => {
  const { token } = theme.useToken();
  const tooltipContentStyle = useTooltipContentStyle();
  const animationActive = useChartAnimation(animationDuration);
  const fill = token[color];
  const barWidth = token[BAR_SIZE_TOKEN[size]];

  const containerRef = useRef<HTMLDivElement>(null);
  const { width: containerWidth } = useContainerSize(containerRef);

  const chartData = data ?? [];

  const derivedIntervalMs = deriveInterval(chartData);
  const timeRangeMs =
    chartData.length >= 2
      ? new Date(chartData[chartData.length - 1].label).getTime() -
        new Date(chartData[0].label).getTime()
      : 0;

  // Stable ref prevents oscillation: re-bucketed data shifts range
  // slightly due to bucket alignment, triggering a feedback loop.
  const stableRangeMsRef = useRef(0);
  useEffect(() => {
    if (timeRangeMs > 0 && stableRangeMsRef.current === 0) {
      stableRangeMsRef.current = timeRangeMs;
    }
  }, [timeRangeMs]);

  const prevRequestRef = useRef<string | null>(null);
  useEffect(() => {
    if (
      !onIntervalChange ||
      containerWidth <= 0 ||
      stableRangeMsRef.current <= 0
    ) {
      return;
    }

    const request = computeDataRequest(
      containerWidth,
      barWidth,
      stableRangeMsRef.current,
    );
    const key = `${request.interval}:${request.rangeMs}`;

    if (key !== prevRequestRef.current) {
      prevRequestRef.current = key;
      onIntervalChange(request);
    }
  }, [onIntervalChange, containerWidth, barWidth]);

  const barCount = chartData.length;
  const slotWidth =
    barCount > 0 && containerWidth > 0
      ? containerWidth / barCount
      : LABEL_WIDTH;
  const tickInterval = Math.max(0, Math.ceil(LABEL_WIDTH / slotWidth) - 1);

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
                  intervalMs={derivedIntervalMs}
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
                contentStyle={tooltipContentStyle}
                labelFormatter={(label) =>
                  tooltipLabelFormatter(String(label), derivedIntervalMs)
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
