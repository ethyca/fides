import { ArrowRight } from "@carbon/icons-react";
import { Flex, theme, Typography } from "antd/lib";
import React, { type ReactNode, useCallback, useMemo } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION } from "./chart-constants";
import { useChartAnimation } from "./chart-utils";
import { ChartText } from "./ChartText";

export interface StackedBarSegment {
  key: string;
  color: AntColorTokenKey;
  label: string;
}

export interface StackedBarChartProps {
  data: Record<string, Record<string, number>>;
  segments: readonly StackedBarSegment[];
  onCategoryClick?: (category: string) => void;
  animationDuration?: number;
}

interface ChartEntry {
  category: string;
  rawCategory: string;
  total: number;
  [key: string]: string | number;
}

const { Text } = Typography;

const StackedBarTooltipContent = ({
  active,
  payload,
  segments,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartEntry }>;
  segments: readonly StackedBarSegment[];
}): ReactNode => {
  const { token } = theme.useToken();

  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload;

  return (
    <Flex
      vertical
      gap={2}
      style={{
        borderRadius: token.borderRadius,
        backgroundColor: token.colorBgElevated,
        padding: `${token.paddingXXS}px ${token.paddingXS}px`,
        boxShadow: token.boxShadow,
        fontSize: token.fontSizeSM,
      }}
    >
      <Text strong>{entry.category}</Text>
      {segments
        .filter((segment) => (entry[`raw_${segment.key}`] as number) > 0)
        .map((segment) => (
          <Text key={segment.key} type="secondary">
            {segment.label}: {entry[`raw_${segment.key}`]}
          </Text>
        ))}
    </Flex>
  );
};

interface ClickableTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  onCategoryClick?: (category: string) => void;
  textColor: string;
  linkColor: string;
  fontSize: number;
  chartData: ChartEntry[];
}

const ICON_SIZE = 12;
const ICON_GAP = 2;

const ClickableTick = ({
  x = 0,
  y = 0,
  payload,
  onCategoryClick,
  textColor,
  linkColor,
  fontSize,
  chartData,
}: ClickableTickProps) => {
  const label = payload?.value ?? "";
  const entry = chartData.find((item) => item.category === label);
  const rawCategory = entry?.rawCategory ?? label.toLowerCase();
  const interactive = !!onCategoryClick;
  const color = interactive ? linkColor : textColor;

  const handleClick = useCallback(() => {
    if (onCategoryClick) {
      onCategoryClick(rawCategory);
    }
  }, [onCategoryClick, rawCategory]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick],
  );

  return (
    <g
      onClick={interactive ? handleClick : undefined}
      onKeyDown={interactive ? handleKeyDown : undefined}
      role={interactive ? "link" : undefined}
      tabIndex={interactive ? 0 : undefined}
      aria-label={interactive ? `View ${label} requests` : undefined}
      style={interactive ? { cursor: "pointer" } : undefined}
    >
      <ChartText
        x={x - (interactive ? ICON_SIZE + ICON_GAP + 4 : 4)}
        y={y}
        textAnchor="end"
        verticalAnchor="middle"
        fontSize={fontSize}
        fill={color}
        width={undefined}
      >
        {label}
      </ChartText>
      {interactive && (
        <foreignObject
          x={x - ICON_SIZE - 2}
          y={y - ICON_SIZE / 2}
          width={ICON_SIZE}
          height={ICON_SIZE}
        >
          <ArrowRight size={ICON_SIZE} color={color} />
        </foreignObject>
      )}
    </g>
  );
};

export const StackedBarChart = ({
  data,
  segments,
  onCategoryClick,
  animationDuration = CHART_ANIMATION.defaultDuration,
}: StackedBarChartProps) => {
  const { token } = theme.useToken();
  const animationActive = useChartAnimation(animationDuration);

  const barHeight = token.sizeLG;
  const rowGap = token.sizeXS;

  const colorMap = useMemo(
    () =>
      Object.fromEntries(
        segments.map((segment) => [segment.key, token[segment.color]]),
      ) as Record<string, string>,
    [token, segments],
  );

  const chartData = useMemo(() => {
    return Object.entries(data)
      .map(([category, row]) => {
        const total = segments.reduce(
          (sum, segment) => sum + (row[segment.key] ?? 0),
          0,
        );
        if (total === 0) {
          return null;
        }
        const entry: ChartEntry = {
          category: category.charAt(0).toUpperCase() + category.slice(1),
          rawCategory: category,
          total,
        };
        segments.forEach((segment) => {
          const raw = row[segment.key] ?? 0;
          entry[segment.key] = (raw / total) * 100;
          entry[`raw_${segment.key}`] = raw;
        });
        return entry;
      })
      .filter((entry): entry is ChartEntry => entry !== null);
  }, [data, segments]);

  // Sort alphabetically so ordering is deterministic (e.g. Access before Erasure)
  const sortedData = useMemo(
    () => [...chartData].sort((a, b) => a.category.localeCompare(b.category)),
    [chartData],
  );

  // Compute YAxis width dynamically from the longest label
  const yAxisWidth = useMemo(() => {
    if (sortedData.length === 0) return 80;
    const longestLabel = sortedData.reduce(
      (max, entry) =>
        entry.category.length > max.length ? entry.category : max,
      "",
    );
    const charWidth = token.fontSizeSM * 0.65;
    const iconSpace = onCategoryClick ? ICON_SIZE + ICON_GAP + 8 : 8;
    return Math.ceil(longestLabel.length * charWidth + iconSpace);
  }, [sortedData, token.fontSizeSM, onCategoryClick]);

  if (sortedData.length === 0) {
    return null;
  }

  const chartHeight =
    sortedData.length * barHeight + (sortedData.length - 1) * rowGap + rowGap;

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={sortedData}
        layout="vertical"
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        barCategoryGap={rowGap}
      >
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="category"
          width={yAxisWidth}
          interval={0}
          tick={
            <ClickableTick
              onCategoryClick={onCategoryClick}
              textColor={token.colorTextSecondary}
              linkColor={token.colorPrimary}
              fontSize={token.fontSizeSM}
              chartData={sortedData}
            />
          }
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          cursor={false}
          content={<StackedBarTooltipContent segments={segments} />}
        />
        {segments.map((segment) => (
          <Bar
            key={segment.key}
            dataKey={segment.key}
            stackId="stack"
            barSize={barHeight}
            isAnimationActive={animationDuration > 0 && animationActive}
            animationDuration={animationDuration}
            animationEasing={CHART_ANIMATION.easing}
            radius={0}
            fill={colorMap[segment.key]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};
