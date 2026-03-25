import {
  antTheme,
  Card,
  Flex,
  Icons,
  Skeleton,
  Sparkline,
  Statistic,
} from "fidesui";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/types";

type StatType = "number" | "percent";

const TREND_METRIC_CONFIG = {
  gps_score: { label: "GPS Score", statType: "number" },
  dsr_volume: { label: "DSR Volume", statType: "number" },
  system_coverage: { label: "System Coverage", statType: "percent" },
  classification_health: {
    label: "Classification Health",
    statType: "percent",
  },
} satisfies Record<string, { label: string; statType: StatType }>;

export type TrendMetricKey = keyof typeof TREND_METRIC_CONFIG;

export const TREND_METRIC_KEYS = Object.keys(
  TREND_METRIC_CONFIG,
) as TrendMetricKey[];

interface TrendCardProps {
  metricKey: TrendMetricKey;
  metric: TrendMetric | undefined;
  isLoading: boolean;
}

const formatMetric = (value: number, statType: StatType) => {
  if (statType === "percent") {
    return `${Math.round(value)}`;
  }
  return nFormatter(value);
};

export const TrendCard = ({ metricKey, metric, isLoading }: TrendCardProps) => {
  const { token } = antTheme.useToken();
  const config = TREND_METRIC_CONFIG[metricKey];
  const statType = config?.statType ?? "number";
  const suffix = statType === "percent" ? "%" : undefined;
  const formattedDiff = metric
    ? formatMetric(Math.abs(metric.diff), statType)
    : undefined;

  const renderStats = () => {
    if (isLoading) {
      return <Skeleton active paragraph={false} />;
    }
    if (!metric) {
      return (
        <Statistic value="—" valueStyle={{ color: token.colorTextDisabled }} />
      );
    }
    return (
      <Flex align="baseline" gap="small">
        <Statistic
          value={formatMetric(metric.value, statType)}
          suffix={suffix}
        />
        {metric.diff !== 0 && formattedDiff !== "0" && (
          <Statistic
            trend={metric.diff > 0 ? "up" : "down"}
            value={formattedDiff}
            suffix={suffix}
            prefix={
              metric.diff > 0 ? (
                <Icons.ArrowUp size={12} />
              ) : (
                <Icons.ArrowDown size={12} />
              )
            }
            size="sm"
          />
        )}
      </Flex>
    );
  };

  return (
    <Card
      variant="borderless"
      title={config?.label ?? metricKey}
      className="h-full text-clip"
      cover={
        !isLoading ? (
          <div className="h-16">
            <Sparkline data={metric?.history} />
          </div>
        ) : undefined
      }
      coverPosition="bottom"
    >
      {renderStats()}
    </Card>
  );
};
