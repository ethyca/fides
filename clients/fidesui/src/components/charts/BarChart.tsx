import { theme } from "antd/lib";
import { useEffect, useRef } from "react";
import {
  Bar,
  BarChart as RechartsBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import type {
  AntColorTokenKey,
  BarSize,
  ChartInterval,
} from "./chart-constants";
import { BAR_SIZE_TOKEN, CHART_ANIMATION } from "./chart-constants";
import type { ChartDataRequest } from "./chart-utils";
import {
  computeDataRequest,
  formatTimestamp,
  intervalToMs,
  tooltipLabelFormatter,
  useChartAnimation,
  useContainerWidth,
  useTooltipContentStyle,
} from "./chart-utils";
import { ChartText } from "./ChartText";

export interface BarChartDataPoint {
  label: string;
  value: number;
}

export interface BarChartProps {
  data?: BarChartDataPoint[];
  color?: AntColorTokenKey;
  interval?: ChartInterval;
  animationDuration?: number;
  tickFormatter?: (label: string) => string;
  showTooltip?: boolean;
  size?: BarSize;
  timeRangeMs?: number;
  onDataRequest?: (request: ChartDataRequest) => void;
}

export const BarChart = ({
  data,
  color = "colorText",
  interval,
  animationDuration = CHART_ANIMATION.defaultDuration,
  tickFormatter,
  showTooltip = true,
  size = "md",
  timeRangeMs,
  onDataRequest,
}: BarChartProps) => {
  const { token } = theme.useToken();
  const tooltipContentStyle = useTooltipContentStyle();
  const animationActive = useChartAnimation(animationDuration);
  const fill = token[color];
  const barWidth = token[BAR_SIZE_TOKEN[size]];

  const containerRef = useRef<HTMLDivElement>(null);
  const containerWidth = useContainerWidth(containerRef);

  const prevRequestRef = useRef<string | null>(null);
  useEffect(() => {
    if (!onDataRequest || containerWidth <= 0) {
      return;
    }

    const request = computeDataRequest(containerWidth, barWidth, timeRangeMs);
    const key = `${request.interval}:${request.rangeMs}`;

    if (key !== prevRequestRef.current) {
      console.log('REQUEST', request)
      prevRequestRef.current = key;
      onDataRequest(request);
    }
  }, [onDataRequest, containerWidth, barWidth, timeRangeMs]);

  const chartData = data ?? [];
  const chartInterval = interval;
  const chartIntervalMs = chartInterval
    ? intervalToMs(chartInterval)
    : undefined;

  const formatLabel =
    tickFormatter ??
    (chartIntervalMs != null
      ? (label: string) => formatTimestamp(label, chartIntervalMs)
      : undefined);

  const LABEL_WIDTH = 110;
  const barCount = chartData.length;
  const slotWidth =
    barCount > 0 && containerWidth > 0
      ? containerWidth / barCount
      : LABEL_WIDTH;
  const tickInterval = Math.max(0, Math.ceil(LABEL_WIDTH / slotWidth) - 1);

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
      width={LABEL_WIDTH}
    >
      {payload ? (formatLabel?.(payload.value) ?? payload.value) : null}
    </ChartText>
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
              tick={renderTick}
              interval={tickInterval}
              axisLine={false}
              tickLine={false}
            />
            {showTooltip && (
              <Tooltip
                cursor={false}
                contentStyle={tooltipContentStyle}
                labelFormatter={
                  chartIntervalMs != null
                    ? (label) =>
                        tooltipLabelFormatter(String(label), chartIntervalMs)
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
            />
          </RechartsBarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
