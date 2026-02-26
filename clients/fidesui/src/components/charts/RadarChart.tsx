import { theme } from "antd";
import { useId } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION } from "./chart-constants";
import { ChartGradient } from "./ChartGradient";

export type RadarPointStatus = "success" | "warning" | "error";

export interface RadarChartDataPoint {
  subject: string;
  value: number;
  status?: RadarPointStatus;
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
  color?: AntColorTokenKey;
  animationDuration?: number;
}

interface RadarTickProps {
  x?: number;
  y?: number;
  payload?: { value: string; index: number };
  data: RadarChartDataPoint[];
  statusColors: Record<RadarPointStatus, string>;
  chartColor: string;
}

const RadarTick = ({
  x = 0,
  y = 0,
  payload,
  data,
  statusColors,
  chartColor,
}: RadarTickProps) => {
  if (!payload) {
    return null;
  }
  const point = data[payload.index];
  const statusColor = point?.status ? statusColors[point.status] : undefined;

  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={11}
      fontWeight={600}
      fill={statusColor ?? chartColor}
      fillOpacity={statusColor ? 1 : 0.75}
    >
      {payload.value}
    </text>
  );
};

interface RadarDotProps {
  cx?: number;
  cy?: number;
  index?: number;
  data: RadarChartDataPoint[];
  statusColors: Record<RadarPointStatus, string>;
  chartColor: string;
  bgColor: string;
}

const RadarDot = ({
  cx: dotCx = 0,
  cy: dotCy = 0,
  index = 0,
  data,
  statusColors,
  chartColor,
  bgColor,
}: RadarDotProps) => {
  const point = data[index];
  return (
    <circle
      cx={dotCx}
      cy={dotCy}
      r={3.5}
      fill={point?.status ? statusColors[point.status] : chartColor}
      stroke={bgColor}
      strokeWidth={1.5}
    />
  );
};

export const RadarChart = ({
  data,
  color,
  animationDuration = CHART_ANIMATION.defaultDuration,
}: RadarChartProps) => {
  const { token } = theme.useToken();
  const empty = !data?.length;
  const chartColor = color ? token[color] : token.colorText;

  const uid = useId().replace(/:/g, "");
  const gradientId = `radar-gradient-${uid}`;

  const STATUS_COLORS: Record<RadarPointStatus, string> = {
    success: token.colorSuccess,
    warning: token.colorWarning,
    error: token.colorError,
  };

  return (
    <div className="h-full w-full pointer-events-none">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={empty ? EMPTY_PLACEHOLDER_DATA : data}
          cx="50%"
          cy="50%"
          outerRadius="70%"
        >
          <ChartGradient
            id={gradientId}
            color={chartColor}
            type="radial"
            inverse
          />

          <PolarGrid
            stroke={chartColor}
            strokeWidth={0.5}
            strokeOpacity={0.15}
          />

          <PolarRadiusAxis tick={false} axisLine={false} />

          {!empty && (
            <PolarAngleAxis
              dataKey="subject"
              tick={
                <RadarTick
                  data={data!}
                  statusColors={STATUS_COLORS}
                  chartColor={chartColor}
                />
              }
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
            dot={
              !empty ? (
                <RadarDot
                  data={data!}
                  statusColors={STATUS_COLORS}
                  chartColor={chartColor}
                  bgColor={token.colorBgContainer}
                />
              ) : (
                false
              )
            }
            activeDot={false}
            isAnimationActive={!empty}
            animationDuration={animationDuration}
            animationEasing={CHART_ANIMATION.easing}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};
