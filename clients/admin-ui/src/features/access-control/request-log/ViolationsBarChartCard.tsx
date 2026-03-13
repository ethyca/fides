import {
  antTheme,
  Card,
  CHART_ANIMATION,
  CHART_STROKE,
  Flex,
  Statistic,
  Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
// eslint-disable-next-line import/no-extraneous-dependencies
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import type { DataConsumerRequestPoint } from "../types";
import { deriveInterval, formatTimestamp, tooltipLabelFormatter, useTooltipContentStyle, XAxisTick } from "../utils";

const { Text } = Typography;

interface ViolationsBarChartCardProps {
  data: DataConsumerRequestPoint[];
  totalViolations: number;
  loading?: boolean;
}

export const ViolationsBarChartCard = ({
  data,
  totalViolations,
  loading,
}: ViolationsBarChartCardProps) => {
  const { token } = antTheme.useToken();
  const intervalMs = deriveInterval(data);
  const tooltipContentStyle = useTooltipContentStyle();

  return (
    <Card loading={loading}>
      <div className="mb-2">
        <Text type="secondary" className="text-xs font-semibold">
          Violations over time
        </Text>
        <Flex align="baseline" gap="small" className="mt-1">
          <Statistic
            value={totalViolations}
            valueStyle={{ fontSize: 28, fontWeight: 700 }}
          />
          <Text type="secondary" className="text-sm">
            Total violations
          </Text>
        </Flex>
      </div>
      <div className="h-[120px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            barCategoryGap="8%"
          >
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
              contentStyle={tooltipContentStyle}
              labelFormatter={(label) => tooltipLabelFormatter(label, intervalMs)}
            />
            <Bar
              dataKey="violations"
              name="Violations"
              fill={palette.FIDESUI_MINOS}
              radius={[1, 1, 0, 0]}
              isAnimationActive={CHART_ANIMATION.defaultDuration > 0}
              animationDuration={CHART_ANIMATION.defaultDuration}
              animationEasing={CHART_ANIMATION.easing}
              maxBarSize={CHART_STROKE.strokeWidth * 8}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
