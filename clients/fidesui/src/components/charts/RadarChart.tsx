import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from "recharts";

import palette from "../../palette/palette.module.scss";

export interface RadarChartDataPoint {
  subject: string;
  value: number;
}

export interface RadarChartProps {
  data: RadarChartDataPoint[];
  color?: string;
  animationDuration?: number;
}

interface CustomTickProps {
  x: number;
  y: number;
  payload: { value: string; index: number };
  activeIndex: number | null;
  color: string;
  filterId: string;
}

const CustomTick = ({
  x,
  y,
  payload,
  activeIndex,
  color,
  filterId,
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
      fill={isActive ? color : palette.FIDESUI_NEUTRAL_500}
      filter={isActive ? `url(#${filterId})` : undefined}
      style={{
        transition: "fill 0.2s ease, font-weight 0.2s ease",
        pointerEvents: "none",
      }}
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
  const index = Math.round(angle / sliceAngle) % dataLength;
  return index;
};

/** Linear interpolation */
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const RadarChart = ({
  data,
  color = palette.FIDESUI_NEUTRAL_900,
  animationDuration = 1500,
}: RadarChartProps) => {
  const [animationKey, setAnimationKey] = useState(0);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Animated focal point state
  const [focalPoint, setFocalPoint] = useState({ fx: 50, fy: 50 });
  const targetFocal = useRef({ fx: 50, fy: 50 });
  const currentFocal = useRef({ fx: 50, fy: 50 });
  const rafId = useRef<number | null>(null);

  const gradientId = useMemo(
    () => `radar-gradient-${Math.random().toString(36).slice(2, 9)}`,
    [],
  );

  const filterId = useMemo(
    () => `radar-glow-${Math.random().toString(36).slice(2, 9)}`,
    [],
  );

  const handleClick = useCallback(() => {
    setAnimationKey((prev) => prev + 1);
  }, []);

  // Compute target focal point when activeIndex changes
  useEffect(() => {
    if (activeIndex === null) {
      targetFocal.current = { fx: 50, fy: 50 };
    } else {
      // Recharts radar starts from top (90° in standard math = -π/2),
      // and goes clockwise. Each point is spaced evenly.
      const angle =
        ((2 * Math.PI) / data.length) * activeIndex - Math.PI / 2;
      const offset = 0.3;
      const fx = 50 + Math.cos(angle) * offset * 100;
      const fy = 50 + Math.sin(angle) * offset * 100;
      targetFocal.current = { fx, fy };
    }
  }, [activeIndex, data.length]);

  // RAF loop for smooth interpolation
  useEffect(() => {
    const animate = () => {
      const speed = 0.12;
      const nextFx = lerp(
        currentFocal.current.fx,
        targetFocal.current.fx,
        speed,
      );
      const nextFy = lerp(
        currentFocal.current.fy,
        targetFocal.current.fy,
        speed,
      );

      currentFocal.current = { fx: nextFx, fy: nextFy };

      rafId.current = requestAnimationFrame(animate);
    };

    rafId.current = requestAnimationFrame(animate);
    return () => {
      if (rafId.current !== null) {
        cancelAnimationFrame(rafId.current);
      }
    };
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const container = containerRef.current;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;

      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 8) {
        setActiveIndex(null);
        return;
      }

      const index = getClosestIndex(dx, dy, data.length);
      setActiveIndex(index);
    },
    [data.length],
  );

  const handleMouseLeave = useCallback(() => {
    setActiveIndex(null);
  }, []);

  return (
    <div
      ref={containerRef}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ width: "100%", height: "100%", cursor: "pointer" }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          key={animationKey}
          data={data}
          cx="50%"
          cy="50%"
          outerRadius="70%"
        >
          <defs>
            <radialGradient
              id={gradientId}
              cx="50%"
              cy="50%"
              r="50%"
              fx={`${focalPoint.fx}%`}
              fy={`${focalPoint.fy}%`}
            >
              <stop offset="0%" stopColor={color} stopOpacity={0.02} />
              <stop
                offset="100%"
                stopColor={color}
                stopOpacity={activeIndex !== null ? 0.35 : 0.2}
              />
            </radialGradient>
            <filter
              id={filterId}
              x="-50%"
              y="-50%"
              width="200%"
              height="200%"
            >
              <feGaussianBlur
                in="SourceGraphic"
                stdDeviation="2"
                result="blur"
              />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          <PolarGrid
            stroke={palette.FIDESUI_NEUTRAL_200}
            strokeWidth={0.5}
          />
          <PolarAngleAxis
            dataKey="subject"
            tick={(props: Record<string, unknown>) => (
              <CustomTick
                {...(props as Omit<
                  CustomTickProps,
                  "activeIndex" | "color" | "filterId"
                >)}
                activeIndex={activeIndex}
                color={color}
                filterId={filterId}
              />
            )}
          />
          <Radar
            dataKey="value"
            stroke={color}
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
                  fill={color}
                  stroke="none"
                  style={{
                    transition: "r 0.2s ease, opacity 0.2s ease",
                    opacity: isActive ? 1 : 0,
                  }}
                />
              );
            }}
            activeDot={false}
            isAnimationActive
            animationDuration={animationDuration}
            animationEasing="ease-in-out"
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RadarChart;
