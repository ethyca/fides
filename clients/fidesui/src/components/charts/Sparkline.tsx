import { theme } from "antd/lib";
import type { CurveType } from "recharts/types/shape/Curve";
import { useId, useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, CHART_STROKE } from "./chart-constants";
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
}

export const Sparkline = ({
  data,
  color,
  strokeWidth = CHART_STROKE.strokeWidth,
  animationDuration = CHART_ANIMATION.defaultDuration,
  interpolation = "monotone",
  xAxisLabels,
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
      label: xAxisLabels?.[i] ?? "",
    }));
  }, [data, empty, xAxisLabels]);

  const showXAxis = !empty && xAxisLabels && xAxisLabels.length > 0;
  const bottomMargin = showXAxis ? 18 : strokeWidth;

  /** Pick evenly spaced tick labels: first, middle, last (3 ticks). */
  const xAxisTicks = useMemo(() => {
    if (!showXAxis) {
      return undefined;
    }
    const len = chartData.length;
    if (len <= 3) {
      return chartData.map((d) => d.label);
    }
    const mid = Math.floor(len / 2);
    return [chartData[0].label, chartData[mid].label, chartData[len - 1].label];
  }, [showXAxis, chartData]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{
          top: strokeWidth,
          right: 20,
          bottom: bottomMargin,
          left: 20,
        }}
      >
        <ChartGradient id={gradientId} color={chartColor} />
        <YAxis domain={["dataMin", "dataMax"]} hide />
        {showXAxis && (
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={{ stroke: token.colorTextTertiary, strokeWidth: 1 }}
            tick={{ fontSize: 10, fill: token.colorTextTertiary }}
            ticks={xAxisTicks}
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
          activeDot={false}
          isAnimationActive={!empty && animationDuration > 0 && animationActive}
          animationDuration={animationDuration}
          animationEasing={CHART_ANIMATION.easing}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};
