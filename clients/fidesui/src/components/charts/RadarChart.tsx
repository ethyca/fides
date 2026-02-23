import { theme } from "antd";
import { useCallback, useId, useRef, useState } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from "recharts";

export interface RadarChartDataPoint {
  subject: string;
  value: number;
}

const EMPTY_PLACEHOLDER_DATA: RadarChartDataPoint[] = [
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
];

export interface RadarChartProps {
  data?: RadarChartDataPoint[] | null;
  color?: string;
  animationDuration?: number;
}

interface CustomTickProps {
  x: number;
  y: number;
  payload: { value: string; index: number };
  activeIndex: number | null;
  color: string;
  className: string;
}

const CustomTick = ({
  x,
  y,
  payload,
  activeIndex,
  color,
  className,
}: CustomTickProps) => {
  const isActive = activeIndex === payload.index;

  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={11}
      fontWeight={isActive ? 600 : 400}
      fill={color}
      fillOpacity={isActive ? 1 : 0.45}
      className={className}
    >
      {payload.value}
    </text>
  );
};

/**
 * Given the cursor position relative to the chart center, compute the angle
 * (in radians, 0 = top / north, clockwise) and return the index of the
 * closest data point.
 */
const getClosestIndex = (
  dx: number,
  dy: number,
  dataLength: number,
): number => {
  let angle = Math.atan2(dx, -dy);
  if (angle < 0) {
    angle += 2 * Math.PI;
  }
  const sliceAngle = (2 * Math.PI) / dataLength;
  return Math.round(angle / sliceAngle) % dataLength;
};

const RadarChart = ({
  data,
  color,
  animationDuration = 1500,
}: RadarChartProps) => {
  const { token } = theme.useToken();
  const empty = !data?.length;
  const chartColor = color ?? token.colorText;

  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const uid = useId().replace(/:/g, "");
  const gradientId = `radar-gradient-${uid}`;
  const textClass = `radar-text-${uid}`;
  const dotClass = `radar-dot-${uid}`;
  const stopClass = `radar-stop-${uid}`;

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!data?.length || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;

      if (Math.sqrt(dx * dx + dy * dy) < 8) {
        setActiveIndex(null);
        return;
      }

      setActiveIndex(getClosestIndex(dx, dy, data.length));
    },
    [data],
  );

  const handleMouseLeave = useCallback(() => {
    setActiveIndex(null);
  }, []);

  return (
    <div
      ref={containerRef}
      className="h-full w-full"
      onMouseMove={empty ? undefined : handleMouseMove}
      onMouseLeave={empty ? undefined : handleMouseLeave}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={empty ? EMPTY_PLACEHOLDER_DATA : data}
          cx="50%"
          cy="50%"
          outerRadius="70%"
        >
          <defs>
            <style>{`
              .${textClass} {
                transition: fill 0.2s ease, fill-opacity 0.2s ease, font-weight 0.2s ease;
                pointer-events: none;
              }
              .${dotClass} {
                transition: r 0.2s ease, opacity 0.2s ease;
              }
              .${stopClass} {
                transition: stop-opacity 0.3s ease;
              }
            `}</style>
            <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={chartColor} stopOpacity={0.02} />
              <stop
                offset="100%"
                stopColor={chartColor}
                stopOpacity={activeIndex !== null ? 0.35 : 0.2}
                className={stopClass}
              />
            </radialGradient>
          </defs>
          <PolarGrid
            stroke={chartColor}
            strokeWidth={0.5}
            strokeOpacity={0.15}
          />
          {!empty && (
            <PolarAngleAxis
              dataKey="subject"
              tick={(props: Record<string, unknown>) => (
                <CustomTick
                  {...(props as Omit<
                    CustomTickProps,
                    "activeIndex" | "color" | "className"
                  >)}
                  activeIndex={activeIndex}
                  color={chartColor}
                  className={textClass}
                />
              )}
            />
          )}
          <Radar
            dataKey="value"
            stroke={chartColor}
            strokeWidth={1.5}
            strokeOpacity={0.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill={`url(#${gradientId})`}
            dot={(props: Record<string, unknown>) => {
              const { cx: dotCx, cy: dotCy, index } = props as {
                cx: number;
                cy: number;
                index: number;
              };
              const isActive = index === activeIndex;
              return (
                <circle
                  key={`dot-${index}`}
                  cx={dotCx}
                  cy={dotCy}
                  r={isActive ? 3.5 : 0}
                  fill={chartColor}
                  stroke="none"
                  opacity={isActive ? 1 : 0}
                  className={dotClass}
                />
              );
            }}
            activeDot={false}
            isAnimationActive={!empty}
            animationDuration={animationDuration}
            animationEasing="ease-in-out"
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RadarChart;
