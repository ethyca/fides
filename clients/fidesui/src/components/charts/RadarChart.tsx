import { theme } from "antd/lib";
import classNames from "classnames";
import type { ReactNode } from "react";
import { useCallback, useId, useMemo, useRef, useState } from "react";
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

const EMPTY_GRID_DATA = [{ value: 100 }, { value: 100 }, { value: 100 }];

const TICK_HIT_WIDTH = 80;
const TICK_HIT_HEIGHT = 20;
const DOT_HIT_RADIUS = 20;

export interface RadarChartProps {
  data?: RadarChartDataPoint[] | null;
  color?: AntColorTokenKey;
  animationDuration?: number;
  outerRadius?: string;
  showGrid?: boolean;
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
  onTickHover?: (
    index: number,
    rect: { x: number; y: number },
    event: React.MouseEvent,
  ) => void;
  onTickLeave?: () => void;
}

const RadarTick = ({
  x = 0,
  y = 0,
  payload,
  data,
  statusColors,
  chartColor,
  onDimensionClick,
  onTickHover,
  onTickLeave,
}: RadarTickProps) => {
  if (!payload) {
    return null;
  }
  const point = data[payload.index];
  const statusColor = point?.status ? statusColors[point.status] : undefined;
  const interactive = !!onDimensionClick || !!onTickHover;

  return (
    <g
      className={classNames({
        "radar-status-error": point?.status === "error",
        [styles.interactive]: interactive,
      })}
      onClick={
        onDimensionClick
          ? () => onDimensionClick(payload.index, point)
          : undefined
      }
      onMouseEnter={
        onTickHover
          ? (e) => onTickHover(payload.index, { x, y }, e)
          : undefined
      }
      onMouseLeave={onTickLeave}
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
        maxLines={2}
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
  showGrid = true,
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

  const containerRef = useRef<HTMLDivElement>(null);

  const [tickTooltip, setTickTooltip] = useState<{
    index: number;
    x: number;
    y: number;
  } | null>(null);

  const handleTickHover = useCallback(
    (index: number, _rect: { x: number; y: number }, e: React.MouseEvent) => {
      if (!tooltipContent || !containerRef.current) {
        return;
      }
      const containerRect = containerRef.current.getBoundingClientRect();
      const clientX = e.clientX - containerRect.left;
      const clientY = e.clientY - containerRect.top;
      setTickTooltip({ index, x: clientX, y: clientY });
    },
    [tooltipContent],
  );

  const handleTickLeave = useCallback(() => {
    setTickTooltip(null);
  }, []);

  const tickTooltipStyle = useMemo<React.CSSProperties>(
    () => ({
      backgroundColor: token.colorBgElevated,
      borderRadius: token.borderRadius,
      padding: `${token.paddingXXS}px ${token.paddingXS}px`,
      boxShadow: token.boxShadow,
      fontSize: token.fontSizeSM,
    }),
    [token],
  );

  return (
    <div
      ref={containerRef}
      className={classNames("w-full h-full relative", className, {
        "pointer-events-none": !interactive,
      })}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={empty ? EMPTY_GRID_DATA : data}
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
          {showGrid && (
            <PolarGrid
              stroke={chartColor}
              strokeWidth={CHART_STROKE.strokeWidth * 0.25}
              strokeOpacity={CHART_STROKE.strokeOpacity * 0.25}
              gridType="circle"
            />
          )}

          <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />

          {empty && <Radar dataKey="value" fill="none" stroke="none" />}

          {!empty && (
            <Radar
              dataKey="value"
              stroke={chartColor}
              strokeWidth={CHART_STROKE.strokeWidth}
              strokeOpacity={CHART_STROKE.strokeOpacity}
              strokeLinecap={CHART_STROKE.strokeLinecap}
              strokeLinejoin={CHART_STROKE.strokeLinejoin}
              fill={`url(#${gradientId})`}
              dot={
                <RadarDot
                  data={data!}
                  statusColors={STATUS_COLORS}
                  chartColor={chartColor}
                  bgColor={token.colorBgContainer}
                  onDimensionClick={onDimensionClick}
                />
              }
              activeDot={false}
              isAnimationActive={animationDuration > 0 && animationActive}
              animationDuration={animationDuration}
              animationEasing={CHART_ANIMATION.easing}
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
                  onTickHover={tooltipContent ? handleTickHover : undefined}
                  onTickLeave={tooltipContent ? handleTickLeave : undefined}
                />
              }
            />
          )}

          {interactive && !empty && !tickTooltip && (
            <Tooltip
              cursor={false}
              content={<RadarTooltipContent tooltipContent={tooltipContent} />}
            />
          )}
        </RechartsRadarChart>
      </ResponsiveContainer>

      {tickTooltip && data?.[tickTooltip.index] && tooltipContent && (
        <div
          style={{
            ...tickTooltipStyle,
            position: "absolute",
            left: tickTooltip.x,
            top: tickTooltip.y,
            transform: "translate(-50%, -100%) translateY(-8px)",
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          {tooltipContent(data[tickTooltip.index])}
        </div>
      )}
    </div>
  );
};
