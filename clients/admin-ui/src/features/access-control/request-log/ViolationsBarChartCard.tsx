import {
  antTheme,
  Card,
  CHART_ANIMATION,
  CHART_STROKE,
  ChartText,
  Flex,
  Statistic,
} from "fidesui";
import { useId, useState } from "react";
// eslint-disable-next-line import/no-extraneous-dependencies
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import type { DataConsumerRequestPoint } from "../types";
import { formatTimestamp } from "../utils";

const deriveInterval = (data: DataConsumerRequestPoint[]): number => {
  if (data.length < 2) {
    return 3_600_000;
  }
  return (
    new Date(data[1].timestamp).getTime() -
    new Date(data[0].timestamp).getTime()
  );
};

interface XAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  intervalMs: number;
  fill?: string;
}

const XAxisTick = ({ x, y, payload, intervalMs, fill }: XAxisTickProps) => (
  <ChartText x={Number(x)} y={Number(y) + 12} fill={fill}>
    {payload ? formatTimestamp(payload.value, intervalMs) : null}
  </ChartText>
);

const ACTIVE_OPACITY = 0.85;
const INACTIVE_OPACITY = 0.25;
const DEFAULT_OPACITY = 0.6;

interface ViolationsBarChartCardProps {
  data: DataConsumerRequestPoint[];
  totalViolations: number;
  loading?: boolean;
}

const ViolationsBarChartCard = ({
  data,
  totalViolations,
  loading,
}: ViolationsBarChartCardProps) => {
  const { token } = antTheme.useToken();
  const rawId = useId().replace(/:/g, "");
  const gradientActiveId = `bar-active-${rawId}`;
  const gradientInactiveId = `bar-inactive-${rawId}`;
  const gradientDefaultId = `bar-default-${rawId}`;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const intervalMs = deriveInterval(data);

  return (
    <Card loading={loading}>
      <Flex align="center" gap={24}>
        <Statistic
          title="Violations"
          value={totalViolations}
          className="shrink-0"
        />
        <div className="h-[120px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 5, right: 5, bottom: 0, left: 0 }}
              onMouseMove={(state) => {
                if (
                  state &&
                  state.activeTooltipIndex !== undefined &&
                  typeof state.activeTooltipIndex === "number"
                ) {
                  setActiveIndex(state.activeTooltipIndex);
                }
              }}
              onMouseLeave={() => setActiveIndex(null)}
            >
              <defs>
                <linearGradient
                  id={gradientActiveId}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor={token.colorText}
                    stopOpacity={ACTIVE_OPACITY}
                  />
                  <stop
                    offset="100%"
                    stopColor={token.colorText}
                    stopOpacity={ACTIVE_OPACITY * 0.4}
                  />
                </linearGradient>
                <linearGradient
                  id={gradientInactiveId}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor={token.colorText}
                    stopOpacity={INACTIVE_OPACITY}
                  />
                  <stop
                    offset="100%"
                    stopColor={token.colorText}
                    stopOpacity={INACTIVE_OPACITY * 0.4}
                  />
                </linearGradient>
                <linearGradient
                  id={gradientDefaultId}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor={token.colorText}
                    stopOpacity={DEFAULT_OPACITY}
                  />
                  <stop
                    offset="100%"
                    stopColor={token.colorText}
                    stopOpacity={DEFAULT_OPACITY * 0.4}
                  />
                </linearGradient>
              </defs>
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
              <Tooltip
                cursor={false}
                contentStyle={{
                  backgroundColor: token.colorBgElevated,
                  border: `1px solid ${token.colorBorder}`,
                  borderRadius: token.borderRadiusLG,
                  boxShadow: token.boxShadowSecondary,
                }}
                labelFormatter={(label) => {
                  const date = new Date(label);
                  if (intervalMs < 86_400_000) {
                    return date.toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    });
                  }
                  return date.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  });
                }}
              />
              <Bar
                dataKey="violations"
                name="Violations"
                radius={[2, 2, 0, 0]}
                isAnimationActive={CHART_ANIMATION.defaultDuration > 0}
                animationDuration={CHART_ANIMATION.defaultDuration}
                animationEasing={CHART_ANIMATION.easing}
                maxBarSize={CHART_STROKE.strokeWidth * 8}
              >
                {data.map((entry, index) => {
                  let gradientRef = gradientDefaultId;
                  if (activeIndex !== null) {
                    gradientRef =
                      index === activeIndex
                        ? gradientActiveId
                        : gradientInactiveId;
                  }
                  return (
                    <Cell key={entry.timestamp} fill={`url(#${gradientRef})`} />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Flex>
    </Card>
  );
};

export { ViolationsBarChartCard };
