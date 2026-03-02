import { theme } from "antd/lib";
import { useEffect, useId, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, CHART_STROKE } from "./chart-constants";
import { ChartGradient } from "./ChartGradient";

const EMPTY_PLACEHOLDER_DATA = [5, 15, 10, 20, 25];

export interface SparklineProps {
  data?: number[] | null;
  color?: AntColorTokenKey;
  strokeWidth?: number;
  animationDuration?: number;
}

export const Sparkline = ({
  data,
  color,
  strokeWidth = CHART_STROKE.strokeWidth,
  animationDuration = CHART_ANIMATION.defaultDuration,
}: SparklineProps) => {
  const { token, hashId } = theme.useToken();
  const empty = !data?.length;
  const activeColor = color ? token[color] : token.colorText;
  const chartColor = empty ? token.colorBorder : activeColor;

  const gradientId = `sparkline-gradient-${useId()}`;

  const [animationActive, setAnimationActive] = useState(true);
  useEffect(() => {
    if (animationDuration <= 0) return;
    const timer = setTimeout(() => setAnimationActive(false), animationDuration);
    return () => clearTimeout(timer);
  }, [animationDuration]);

  const chartData = (empty ? EMPTY_PLACEHOLDER_DATA : data).map((v) => ({
    value: v,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        key={hashId}
        data={chartData}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
      >
        <ChartGradient id={gradientId} color={chartColor} />
        <YAxis domain={["dataMin", "dataMax"]} hide />
        <Area
          type="monotone"
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
