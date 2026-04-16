import { theme } from "antd/lib";
import type { ReactNode } from "react";
import { useCallback, useId, useMemo } from "react";
import type { XAxisTickContentProps } from "recharts";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CurveType } from "recharts/types/shape/Curve";

import type { AntColorTokenKey } from "./chart-constants";
import {
  CHART_ANIMATION,
  CHART_STROKE,
  CHART_TYPOGRAPHY,
} from "./chart-constants";
import { useChartAnimation } from "./chart-utils";
import { ChartGradient } from "./ChartGradient";

const EMPTY_PLACEHOLDER_DATA = [5, 15, 10, 20, 25];

export interface SparklineProps {
  data?: number[] | null;
  color?: AntColorTokenKey;
  strokeWidth?: number;
  animationDuration?: number;
  /** Recharts interpolation type. Defaults to "monotone". Use "linear" for less smoothing. */
  interpolation?: CurveType;
  /** Optional labels for x-axis ticks, one per data point. When provided, an XAxis is rendered. */
  xAxisLabels?: string[];
  /** When provided, enables a cursor tooltip on hover. Receives the value and label for the hovered point. */
  tooltipContent?: (value: number, label: string) => ReactNode;
}

export const Sparkline = ({
  data,
  color,
  strokeWidth = CHART_STROKE.strokeWidth,
  animationDuration = CHART_ANIMATION.defaultDuration,
  interpolation = "monotone",
  xAxisLabels,
  tooltipContent,
}: SparklineProps) => {
  const { token } = theme.useToken();
  const empty = !data || data.length <= 1;
  const activeColor = color ? token[color] : token.colorText;
  const chartColor = empty ? token.colorBorder : activeColor;

  const gradientId = `sparkline-gradient-${useId()}`;

  const animationActive = useChartAnimation(animationDuration);

  const chartData = useMemo(() => {
    const values = empty ? EMPTY_PLACEHOLDER_DATA : data;
    return values.map((v, i) => ({
      value: v,
      idx: i,
    }));
  }, [data, empty]);

  const showXAxis = !empty && xAxisLabels && xAxisLabels.length > 0;
  const bottomMargin = strokeWidth;

  /** Pick 3 evenly spaced interior tick positions using exact fractions for perfect spacing. */
  const xAxisTickPositions = useMemo(() => {
    if (!showXAxis) {
      return undefined;
    }
    const last = chartData.length - 1;
    return [last * 0.25, last * 0.5, last * 0.75];
  }, [showXAxis, chartData]);

  const renderXAxisTick = useCallback(
    (tickProps: XAxisTickContentProps) => {
      const idx = Math.round(Number(tickProps.payload.value));
      const label = xAxisLabels?.[idx] ?? "";
      return (
        <text
          x={tickProps.x}
          y={Number(tickProps.y) + 10}
          fontSize={token.fontSizeSM}
          fontFamily={token.fontFamilyCode}
          fontWeight={CHART_TYPOGRAPHY.fontWeight}
          letterSpacing={CHART_TYPOGRAPHY.letterSpacing}
          fill={token.colorTextTertiary}
          textAnchor="middle"
        >
          {label}
        </text>
      );
    },
    [xAxisLabels, token],
  );

  const renderTooltipContent = useCallback(
    (tooltipProps: {
      payload?: ReadonlyArray<{ payload: { value: number; idx: number } }>;
    }) => {
      const { payload } = tooltipProps;
      if (!payload?.length) {
        return null;
      }
      const entry = payload[0].payload;
      const label = xAxisLabels?.[entry.idx] ?? "";
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
          {tooltipContent!(entry.value, label)}
        </div>
      );
    },
    [xAxisLabels, token, tooltipContent],
  );

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{
          top: strokeWidth,
          right: 0,
          bottom: bottomMargin,
          left: 0,
        }}
      >
        <ChartGradient id={gradientId} color={chartColor} />
        <YAxis domain={["dataMin", "dataMax"]} hide />
        {showXAxis && (
          <XAxis
            dataKey="idx"
            type="number"
            domain={[0, chartData.length - 1]}
            axisLine={false}
            tickLine={{ stroke: token.colorTextTertiary, strokeWidth: 1 }}
            ticks={xAxisTickPositions}
            interval={0}
            tick={renderXAxisTick}
          />
        )}
        <Area
          type={interpolation}
          dataKey="value"
          stroke={chartColor}
          strokeWidth={strokeWidth}
          strokeOpacity={CHART_STROKE.strokeOpacity}
          strokeLinecap={CHART_STROKE.strokeLinecap}
          strokeLinejoin={CHART_STROKE.strokeLinejoin}
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={
            !empty && tooltipContent
              ? {
                  r: CHART_STROKE.dotRadius,
                  stroke: token.colorBgContainer,
                  strokeWidth: CHART_STROKE.strokeWidth,
                  fill: chartColor,
                }
              : false
          }
          isAnimationActive={!empty && animationDuration > 0 && animationActive}
          animationDuration={animationDuration}
          animationEasing={CHART_ANIMATION.easing}
        />
        {!empty && tooltipContent && (
          <Tooltip
            cursor={{ stroke: token.colorTextTertiary, strokeWidth: 1 }}
            content={renderTooltipContent}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
};
