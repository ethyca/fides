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
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, CHART_STROKE } from "./chart-constants";
import { useChartAnimation } from "./chart-utils";
import { ChartGradient } from "./ChartGradient";
import { ChartText } from "./ChartText";
import styles from "./RadarChart.module.scss";

export type RadarPointStatus = "success" | "warning" | "error";

export interface RadarChartDataPoint {
  subject: string;
  value: number;
  status?: RadarPointStatus;
  tag?: {
    label: string;
    status?: RadarPointStatus;
  };
}

const EMPTY_GRID_DATA = [{ value: 100 }, { value: 100 }, { value: 100 }];

const TICK_HIT_WIDTH = 80;
const TICK_HIT_HEIGHT = 40;
const DOT_HIT_RADIUS = 20;

const TAG_HEIGHT = 16;
const TAG_PADDING_X = 8;
const TAG_FONT_SIZE = 10;
const TAG_CHAR_WIDTH = 6;

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
  bgColor: string;
  onDimensionClick?: (index: number, point: RadarChartDataPoint) => void;
  onTickHover?: (index: number, event: React.MouseEvent) => void;
  onTickLeave?: () => void;
}

const RadarTick = ({
  x = 0,
  y = 0,
  payload,
  data,
  statusColors,
  chartColor,
  bgColor,
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

  let tagElement: ReactNode = null;
  if (point?.tag) {
    const tagColor = point.tag.status
      ? statusColors[point.tag.status]
      : chartColor;
    const tagWidth = Math.max(
      28,
      point.tag.label.length * TAG_CHAR_WIDTH + TAG_PADDING_X * 2,
    );
    tagElement = (
      <g pointerEvents="none">
        <rect
          x={x - tagWidth / 2}
          y={y + 4}
          width={tagWidth}
          height={TAG_HEIGHT}
          rx={TAG_HEIGHT / 2}
          fill={tagColor}
          fillOpacity={0.15}
        />
        <text
          x={x}
          y={y + 4 + TAG_HEIGHT / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={tagColor}
          fontSize={TAG_FONT_SIZE}
          fontWeight={600}
        >
          {point.tag.label}
        </text>
      </g>
    );
  }

  return (
    <g
      className={classNames({
        "radar-status-error": point?.status === "error",
        [styles.interactive]: interactive,
      })}
    >
      {interactive && (
        <rect
          x={x - TICK_HIT_WIDTH / 2}
          y={y - TICK_HIT_HEIGHT / 2}
          width={TICK_HIT_WIDTH}
          height={TICK_HIT_HEIGHT}
          fill="transparent"
          cursor="pointer"
          onClick={
            onDimensionClick
              ? () => onDimensionClick(payload.index, point)
              : undefined
          }
          onMouseEnter={
            onTickHover ? (e) => onTickHover(payload.index, e) : undefined
          }
          onMouseLeave={onTickLeave}
        />
      )}
      <ChartText
        x={x}
        y={point?.tag ? y - 14 : y}
        fill={statusColor ?? chartColor}
        fillOpacity={1}
        stroke={bgColor}
        strokeWidth={3}
        strokeOpacity={0.5}
        paintOrder="stroke"
        strokeLinejoin="round"
        maxLines={2}
        style={{ pointerEvents: "none" }}
      >
        {payload.value}
      </ChartText>
      {tagElement}
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

  const handleTickHover = useCallback((index: number, e: React.MouseEvent) => {
    if (!containerRef.current) {
      return;
    }
    const rect = containerRef.current.getBoundingClientRect();
    setTickTooltip({
      index,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, []);

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
      lineHeight: 1.3,
    }),
    [token],
  );

  return (
    <div
      ref={containerRef}
      className={classNames("w-full h-full relative", className, {
        "pointer-events-none": !interactive,
        [styles.interactiveContainer]: interactive,
      })}
      onMouseLeave={tooltipContent ? handleTickLeave : undefined}
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
                  bgColor={token.colorBgContainer}
                  onDimensionClick={onDimensionClick}
                  onTickHover={tooltipContent ? handleTickHover : undefined}
                  onTickLeave={tooltipContent ? handleTickLeave : undefined}
                />
              }
            />
          )}
        </RechartsRadarChart>
      </ResponsiveContainer>

      {tickTooltip && data?.[tickTooltip.index] && tooltipContent && (
        <div
          key={tickTooltip.index}
          className={styles.tickTooltip}
          style={{
            ...tickTooltipStyle,
            position: "absolute",
            left: tickTooltip.x,
            top: tickTooltip.y,
            transform: "translate(-50%, -100%) translateY(-8px)",
            pointerEvents: "none",
            zIndex: 10,
            width: 140,
          }}
        >
          {tooltipContent(data[tickTooltip.index])}
        </div>
      )}
    </div>
  );
};
