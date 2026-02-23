import { theme } from "antd";
import { useId } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";

export interface SparklineProps {
  data: { value: number }[];
  color?: string;
  strokeWidth?: number;
  animationDuration?: number;
}

const Sparkline = ({
  data,
  color,
  strokeWidth = 2,
  animationDuration = 600,
}: SparklineProps) => {
  const { token } = theme.useToken();
  const resolvedColor = color ?? token.colorText;

  const gradientId = `sparkline-gradient-${useId()}`;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={data}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={resolvedColor} stopOpacity={0.25} />
            <stop offset="100%" stopColor={resolvedColor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={["dataMin", "dataMax"]} hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke={resolvedColor}
          strokeWidth={strokeWidth}
          strokeOpacity={0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={false}
          isAnimationActive={animationDuration > 0}
          animationDuration={animationDuration}
          animationEasing="ease-in-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default Sparkline;
