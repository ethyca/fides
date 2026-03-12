import {
  antTheme,
  Card,
  CHART_ANIMATION,
  CHART_STROKE,
  ChartText,
  Text,
} from "fidesui";
import { useId } from "react";
// eslint-disable-next-line import/no-extraneous-dependencies
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DataConsumerRequestPoint } from "../types";

const GRADIENT_START_OPACITY = 0.25;
const GRADIENT_END_OPACITY = 0;

const formatXAxisLabel = (timestamp: string, pointCount: number) => {
  const date = new Date(timestamp);
  if (pointCount <= 24) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

interface XAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  pointCount: number;
  fill?: string;
}

const XAxisTick = ({ x, y, payload, pointCount, fill }: XAxisTickProps) => (
  <ChartText x={Number(x)} y={Number(y) + 12} fill={fill}>
    {payload ? formatXAxisLabel(payload.value, pointCount) : null}
  </ChartText>
);

interface ViolationsOverTimeCardProps {
  data: DataConsumerRequestPoint[];
  loading?: boolean;
}

export const ViolationsOverTimeCard = ({
  data,
  loading,
}: ViolationsOverTimeCardProps) => {
  const { token } = antTheme.useToken();
  const violationsGradientId = `violations-gradient-${useId()}`;
  const requestsGradientId = `requests-gradient-${useId()}`;
  const pointCount = data.length;

  return (
    <Card
      loading={loading}
      title={<Text strong>Violations over time</Text>}
      className="h-full flex flex-col"
      styles={{ body: { flex: 1, display: "flex", flexDirection: "column" } }}
    >
      <div className="w-full flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 5, right: 5, bottom: 0, left: -15 }}
          >
            <defs>
              <linearGradient
                id={violationsGradientId}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={token.colorText}
                  stopOpacity={GRADIENT_START_OPACITY}
                />
                <stop
                  offset="100%"
                  stopColor={token.colorText}
                  stopOpacity={GRADIENT_END_OPACITY}
                />
              </linearGradient>
              <linearGradient
                id={requestsGradientId}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={token.colorBorder}
                  stopOpacity={GRADIENT_START_OPACITY}
                />
                <stop
                  offset="100%"
                  stopColor={token.colorBorder}
                  stopOpacity={GRADIENT_END_OPACITY}
                />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={token.colorBorderSecondary}
              vertical={false}
            />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(ts) => formatXAxisLabel(ts, pointCount)}
              tick={
                <XAxisTick
                  pointCount={pointCount}
                  fill={token.colorTextTertiary}
                />
              }
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{
                fontSize: token.fontSizeSM,
                fill: token.colorTextTertiary,
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: token.colorBgElevated,
                border: `1px solid ${token.colorBorder}`,
                borderRadius: token.borderRadiusLG,
                boxShadow: token.boxShadowSecondary,
              }}
              labelFormatter={(label) =>
                new Date(label).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })
              }
            />
            <Area
              type="monotone"
              dataKey="requests"
              name="Total Requests"
              stroke={token.colorBorder}
              strokeWidth={CHART_STROKE.strokeWidth}
              strokeOpacity={CHART_STROKE.strokeOpacity}
              strokeLinecap={CHART_STROKE.strokeLinecap}
              strokeLinejoin={CHART_STROKE.strokeLinejoin}
              fill={`url(#${requestsGradientId})`}
              dot={false}
              activeDot={{ r: CHART_STROKE.dotRadius }}
              isAnimationActive={CHART_ANIMATION.defaultDuration > 0}
              animationDuration={CHART_ANIMATION.defaultDuration}
              animationEasing={CHART_ANIMATION.easing}
            />
            <Area
              type="monotone"
              dataKey="violations"
              name="Violations"
              stroke={token.colorText}
              strokeWidth={CHART_STROKE.strokeWidth}
              strokeOpacity={CHART_STROKE.strokeOpacity}
              strokeLinecap={CHART_STROKE.strokeLinecap}
              strokeLinejoin={CHART_STROKE.strokeLinejoin}
              fill={`url(#${violationsGradientId})`}
              dot={false}
              activeDot={{ r: CHART_STROKE.dotRadius }}
              isAnimationActive={CHART_ANIMATION.defaultDuration > 0}
              animationDuration={CHART_ANIMATION.defaultDuration}
              animationEasing={CHART_ANIMATION.easing}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
