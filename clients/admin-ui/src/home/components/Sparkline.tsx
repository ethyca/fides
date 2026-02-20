import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";

interface SparklineProps {
  data: { value: number }[];
  color?: string;
  strokeWidth?: number;
  showEndDot?: boolean;
}

const Sparkline = ({
  data,
  color = palette.FIDESUI_TERRACOTTA,
  strokeWidth = 1.5,
  showEndDot = true,
}: SparklineProps) => {
  const gradientId = useMemo(
    () => `sparkline-gradient-${Math.random().toString(36).slice(2, 9)}`,
    [],
  );

  const renderDot = (props: { cx?: number; cy?: number; index?: number }) => {
    const { cx, cy, index } = props;
    if (!showEndDot || index !== data.length - 1) {
      return <circle key={`dot-${index}`} r={0} />;
    }
    return (
      <g key={`dot-${index}`}>
        <circle cx={cx} cy={cy} r={6} fill={color} opacity={0.25} />
        <circle cx={cx} cy={cy} r={3} fill={color} />
      </g>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.25} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={["dataMin", "dataMax"]} hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeOpacity={0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill={`url(#${gradientId})`}
          dot={renderDot}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default Sparkline;
