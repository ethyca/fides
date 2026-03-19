import { theme } from "antd/lib";
import classNames from "classnames";
import type { ReactNode } from "react";
import { useId, useMemo } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, CHART_STROKE } from "./chart-constants";
import { useChartAnimation } from "./chart-utils";
import { ChartGradient } from "./ChartGradient";
import { ChartText } from "./ChartText";
import styles from "./RadarChart.module.scss";
import { RadarTooltipContent } from "./RadarTooltipContent";

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

const TICK_HIT_WIDTH = 80;
const TICK_HIT_HEIGHT = 20;
const DOT_HIT_RADIUS = 20;

export interface RadarChartProps {
  data?: RadarChartDataPoint[] | null;
  color?: AntColorTokenKey;
  animationDuration?: number;
  outerRadius?: string;
  onDimensionClick?: (index: number, point: RadarChartDataPoint) => void;
  tooltipContent?: (point: RadarChartDataPoint) => ReactNode;
  className?: string;
}

interface RadarTickProps {
  x?: number;
  y?: number;
  payload?: { value: string; index: number };
  data: RadarChartDataPoint[];
  statusColors: Record<RadarPointStatus, string>;
  chartColor: string;
  onDimensionClick?: (index: number, point: RadarChartDataPoint) => void;
}

const RadarTick = ({
  x = 0,
  y = 0,
  payload,
  data,
  statusColors,
  chartColor,
  onDimensionClick,
}: RadarTickProps) => {
  if (!payload) {
    return null;
  }
  const point = data[payload.index];
  const statusColor = point?.status ? statusColors[point.status] : undefined;
  const interactive = !!onDimensionClick;

  return (
    <g
      className={classNames({
        "radar-status-error": point?.status === "error",
        [styles.interactive]: interactive,
      })}
      onClick={
        interactive ? () => onDimensionClick(payload.index, point) : undefined
      }
    >
      {interactive && (
        <rect
          x={x - TICK_HIT_WIDTH / 2}
          y={y - TICK_HIT_HEIGHT / 2}
          width={TICK_HIT_WIDTH}
          height={TICK_HIT_HEIGHT}
          fill="transparent"
        />
      )}
      <ChartText
        x={x}
        y={y}
        fill={statusColor ?? chartColor}
        fillOpacity={statusColor ? 1 : 0.75}
        fontSize={10}
      >
        {payload.value}
      </ChartText>
    </g>
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
  onDimensionClick?: (index: number, point: RadarChartDataPoint) => void;
}

const RadarDot = ({
  cx: dotCx = 0,
  cy: dotCy = 0,
  index = 0,
  data,
  statusColors,
  chartColor,
  bgColor,
  onDimensionClick,
}: RadarDotProps) => {
  const point = data[index];
  const interactive = !!onDimensionClick;
  return (
    <g
      className={classNames({
        "radar-status-error": point?.status === "error",
        [styles.interactive]: interactive,
      })}
    >
      <circle
        cx={dotCx}
        cy={dotCy}
        r={CHART_STROKE.dotRadius}
        fill={point?.status ? statusColors[point.status] : chartColor}
        stroke={bgColor}
        strokeWidth={CHART_STROKE.strokeWidth}
        pointerEvents="none"
      />
      {interactive && (
        <circle
          cx={dotCx}
          cy={dotCy}
          r={DOT_HIT_RADIUS}
          fill="transparent"
          stroke="none"
          pointerEvents="all"
          onClick={() => onDimensionClick(index, point)}
        />
      )}
    </g>
  );
};

export const RadarChart = ({
  data,
  color,
  outerRadius = "70%",
  animationDuration = CHART_ANIMATION.defaultDuration,
  onDimensionClick,
  tooltipContent,
  className,
}: RadarChartProps) => {
  const { token } = theme.useToken();
  const empty = !data?.length;
  const chartColor = color ? token[color] : token.colorText;

  const gradientId = `radar-gradient-${useId()}`;

  const animationActive = useChartAnimation(animationDuration);

  const STATUS_COLORS = useMemo<Record<RadarPointStatus, string>>(
    () => ({
      success: token.colorSuccess,
      warning: token.colorWarning,
      error: token.colorError,
    }),
    [token],
  );

  const interactive = !!onDimensionClick || !!tooltipContent;

  return (
    <div
      className={classNames("w-full h-full", className, {
        "pointer-events-none": !interactive,
      })}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={empty ? EMPTY_PLACEHOLDER_DATA : data}
          cx="50%"
          cy="50%"
          outerRadius={outerRadius}
        >
          <ChartGradient
            id={gradientId}
            color={chartColor}
            type="radial"
            inverse
          />

          <PolarGrid
            stroke={chartColor}
            strokeWidth={CHART_STROKE.strokeWidth * 0.25}
            strokeOpacity={CHART_STROKE.strokeOpacity * 0.25}
          />

          <PolarRadiusAxis tick={false} axisLine={false} />

          <Radar
            dataKey="value"
            stroke={chartColor}
            strokeWidth={CHART_STROKE.strokeWidth}
            strokeOpacity={CHART_STROKE.strokeOpacity}
            strokeLinecap={CHART_STROKE.strokeLinecap}
            strokeLinejoin={CHART_STROKE.strokeLinejoin}
            fill={`url(#${gradientId})`}
            dot={
              !empty ? (
                <RadarDot
                  data={data!}
                  statusColors={STATUS_COLORS}
                  chartColor={chartColor}
                  bgColor={token.colorBgContainer}
                  onDimensionClick={onDimensionClick}
                />
              ) : (
                false
              )
            }
            activeDot={false}
            isAnimationActive={
              !empty && animationDuration > 0 && animationActive
            }
            animationDuration={animationDuration}
            animationEasing={CHART_ANIMATION.easing}
          />

          {interactive && !empty && (
            <Tooltip
              cursor={false}
              content={<RadarTooltipContent tooltipContent={tooltipContent} />}
            />
          )}

          {!empty && (
            <PolarAngleAxis
              dataKey="subject"
              tick={
                <RadarTick
                  data={data!}
                  statusColors={STATUS_COLORS}
                  chartColor={chartColor}
                  onDimensionClick={onDimensionClick}
                />
              }
            />
          )}
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};
