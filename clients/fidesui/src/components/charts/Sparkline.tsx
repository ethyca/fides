import { GlobalToken, theme } from "antd";
import { useId } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";

const EMPTY_PLACEHOLDER_DATA = [5, 15, 10, 20, 25];

export type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export interface SparklineProps {
  data?: number[] | null;
  color?: AntColorTokenKey;
  strokeWidth?: number;
  animationDuration?: number;
}

export const Sparkline = ({
  data,
  color,
  strokeWidth = 2,
  animationDuration = 600,
}: SparklineProps) => {
  const { token } = theme.useToken();
  const empty = !data?.length;
  const chartColor = empty
    ? token.colorBorder
    : color
      ? token[color]
      : token.colorText;

  const gradientId = `sparkline-gradient-${useId()}`;
  const chartData = (empty ? EMPTY_PLACEHOLDER_DATA : data).map((v) => ({
    value: v,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={chartColor} stopOpacity={0.25} />
            <stop offset="100%" stopColor={chartColor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={["dataMin", "dataMax"]} hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke={chartColor}
          strokeWidth={strokeWidth}
          strokeOpacity={0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={false}
          isAnimationActive={!empty && animationDuration > 0}
          animationDuration={animationDuration}
          animationEasing="ease-in-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};
