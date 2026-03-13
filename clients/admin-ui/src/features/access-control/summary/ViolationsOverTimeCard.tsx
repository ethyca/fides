import {
  antTheme,
  Card,
  CHART_ANIMATION,
  CHART_STROKE,
  Statistic,
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
import {
  deriveInterval,
  formatTimestamp,
  formatTrend,
  tooltipLabelFormatter,
  useTooltipContentStyle,
  XAxisTick,
} from "../utils";

interface ViolationsOverTimeCardProps {
  data: DataConsumerRequestPoint[];
  totalViolations: number;
  trend: number;
  loading?: boolean;
}

export const ViolationsOverTimeCard = ({
  data,
  totalViolations,
  trend,
  loading,
}: ViolationsOverTimeCardProps) => {
  const { token } = antTheme.useToken();
  const violationsGradientId = `violations-gradient-${useId()}`;
  const requestsGradientId = `requests-gradient-${useId()}`;
  const intervalMs = deriveInterval(data);
  const tooltipContentStyle = useTooltipContentStyle();

  return (
    <Card
      loading={loading}
      title={<Text strong>Violations over time</Text>}
      extra={
        <Text
          style={{
            color: trend <= 0 ? token.colorSuccess : token.colorError,
            fontSize: token.fontSizeSM,
          }}
        >
          {formatTrend(trend)}
        </Text>
      }
      className="flex h-full flex-col text-clip"
      styles={{
        body: {
          flex: 1,
          display: "flex",
          flexDirection: "column",
          paddingLeft: 0,
          paddingRight: 0,
          paddingBottom: 0,
        },
      }}
    >
      <div className="px-6">
        <Statistic
          value={totalViolations}
          valueStyle={{
            color: token.colorError,
            fontSize: token.fontSizeHeading2,
          }}
        />
      </div>
      <div className="mt-2 min-h-0 w-full flex-1">
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
                  stopOpacity={0.25}
                />
                <stop
                  offset="100%"
                  stopColor={token.colorText}
                  stopOpacity={0}
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
                  stopOpacity={0.25}
                />
                <stop
                  offset="100%"
                  stopColor={token.colorBorder}
                  stopOpacity={0}
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
              tickFormatter={(ts) => formatTimestamp(ts, intervalMs)}
              tick={
                <XAxisTick
                  intervalMs={intervalMs}
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
              contentStyle={tooltipContentStyle}
              labelFormatter={(label) =>
                tooltipLabelFormatter(label, intervalMs)
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
