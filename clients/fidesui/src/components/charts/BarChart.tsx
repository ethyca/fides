import { theme } from "antd/lib";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef } from "react";
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
  CHART_TYPOGRAPHY,
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
  /** When true, renders 3 evenly spaced interior x-axis labels using the bar labels. */
  simpleXAxis?: boolean;
  /** Custom tooltip renderer. Receives the value and label for the hovered bar. */
  tooltipContent?: (value: number, label: string) => ReactNode;
}

export const BarChart = ({
  data,
  color = "colorText",
  rangeMs,
  onIntervalChange,
  animationDuration = CHART_ANIMATION.defaultDuration,
  showTooltip = true,
  size = "md",
  simpleXAxis = false,
  tooltipContent,
}: BarChartProps) => {
  const { token } = theme.useToken();
  const animationActive = useChartAnimation(animationDuration);
  const fill = token[color];
  const barWidth = token[BAR_SIZE_TOKEN[size]];

  const containerRef = useRef<HTMLDivElement>(null);
  const { width: containerWidth } = useContainerSize(containerRef);

  const onIntervalChangeRef = useRef(onIntervalChange);
  useEffect(() => {
    onIntervalChangeRef.current = onIntervalChange;
  });

  const chartData = data ?? [];

  useEffect(() => {
    if (
      onIntervalChangeRef.current &&
      rangeMs &&
      rangeMs > 0 &&
      containerWidth > 0
    ) {
      onIntervalChangeRef.current(
        pickIntervalHours(rangeMs, containerWidth, barWidth),
      );
    }
  }, [rangeMs, containerWidth, barWidth]);

  const intervalMs = deriveInterval(chartData);
  const tickInterval = calcTickInterval(
    chartData.length,
    containerWidth,
    LABEL_WIDTH,
  );

  /** 3 evenly spaced interior tick indices for simpleXAxis mode. */
  const simpleTickIndices = useMemo(() => {
    if (!simpleXAxis || chartData.length < 4) {
      return undefined;
    }
    const last = chartData.length - 1;
    return new Set([
      Math.round(last * 0.25),
      Math.round(last * 0.5),
      Math.round(last * 0.75),
    ]);
  }, [simpleXAxis, chartData.length]);

  const renderTooltipContent = useCallback(
    ({
      payload,
    }: {
      payload?: ReadonlyArray<{ payload: BarChartDataPoint }>;
    }) => {
      if (!payload?.length) {
        return null;
      }
      const entry = payload[0].payload;
      return (
        <div
          style={{
            backgroundColor: token.colorBgElevated,
            borderRadius: token.borderRadius,
            padding: `${token.paddingXXS}px ${token.paddingXS}px`,
            boxShadow: token.boxShadow,
            fontSize: token.fontSizeSM,
          }}
        >
          {tooltipContent?.(entry.value, entry.label)}
        </div>
      );
    },
    [token, tooltipContent],
  );

  const renderSimpleTick = useCallback(
    (props: Record<string, unknown>) => {
      const index = props.index as number;
      if (!simpleTickIndices?.has(index)) {
        return <g />;
      }
      return (
        <text
          x={Number(props.x)}
          y={Number(props.y) + 10}
          fontSize={token.fontSizeSM}
          fontFamily={token.fontFamilyCode}
          fontWeight={CHART_TYPOGRAPHY.fontWeight}
          letterSpacing={CHART_TYPOGRAPHY.letterSpacing}
          fill={token.colorTextTertiary}
          textAnchor="middle"
        >
          {(props.payload as { value: string }).value}
        </text>
      );
    },
    [simpleTickIndices, token],
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
                simpleXAxis && simpleTickIndices ? (
                  renderSimpleTick
                ) : (
                  <XAxisTick
                    intervalMs={intervalMs}
                    fill={token.colorTextTertiary}
                  />
                )
              }
              interval={simpleXAxis ? 0 : tickInterval}
              axisLine={false}
              tickLine={false}
            />
            {(showTooltip || tooltipContent) && (
              <Tooltip
                cursor={false}
                content={tooltipContent ? renderTooltipContent : undefined}
                contentStyle={
                  !tooltipContent
                    ? {
                        backgroundColor: token.colorBgElevated,
                        border: `1px solid ${token.colorBorder}`,
                        borderRadius: token.borderRadiusLG,
                        boxShadow: token.boxShadowSecondary,
                      }
                    : undefined
                }
                labelFormatter={
                  !tooltipContent
                    ? (label) =>
                        formatTimestamp(String(label), intervalMs, true)
                    : undefined
                }
              />
            )}
            <Bar
              dataKey="value"
              fill={fill}
              barSize={barWidth}
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
