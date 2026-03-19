import {
  antTheme,
  Card,
  CHART_ANIMATION,
  CHART_STROKE,
  ChartGradient,
  deriveInterval,
  formatTimestamp,
  Statistic,
  Text,
  tooltipLabelFormatter,
  useTooltipContentStyle,
  XAxisTick,
} from "fidesui";
import { useId } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TimeseriesBucket } from "../types";

interface ViolationsOverTimeCardProps {
  data: TimeseriesBucket[];
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
        <Statistic
          value={Math.abs(trend * 100)}
          precision={1}
          prefix={trend <= 0 ? "-" : "+"}
          suffix="% vs last mo"
          valueStyle={{
            color: trend <= 0 ? token.colorSuccess : token.colorError,
            fontSize: token.fontSizeSM,
          }}
        />
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
            <ChartGradient id={violationsGradientId} color={token.colorText} />
            <ChartGradient id={requestsGradientId} color={token.colorBorder} />
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={token.colorBorderSecondary}
              vertical={false}
            />
            <XAxis
              dataKey="label"
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
