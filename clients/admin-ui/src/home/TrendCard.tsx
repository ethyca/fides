import classNames from "classnames";
import { Card, Skeleton, Sparkline, Statistic } from "fidesui";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/types";

import cardStyles from "./dashboard-card.module.scss";

type StatType = "number" | "percent";

interface MetricConfig {
  label: string;
  statType: StatType;
}

const TREND_METRIC_CONFIG: Record<string, MetricConfig> = {
  gps_score: { label: "GPS Score", statType: "number" },
  dsr_volume: { label: "DSR Volume", statType: "number" },
  system_coverage: { label: "System Coverage", statType: "percent" },
  classification_health: {
    label: "Classification Health",
    statType: "percent",
  },
};

export type TrendMetricKey = keyof typeof TREND_METRIC_CONFIG;

export const TREND_METRIC_KEYS = Object.keys(TREND_METRIC_CONFIG) as TrendMetricKey[];

interface TrendCardProps {
  metricKey: TrendMetricKey;
  metric: TrendMetric | undefined;
}

const formatValue = (value: number, statType: StatType) => {
  if (statType === "percent") {
    return `${Math.round(value)}`;
  }
  return nFormatter(value);
};

const formatDiff = (diff: number, statType: StatType) => {
  const abs = Math.abs(diff);
  if (statType === "percent") {
    return `${Math.round(abs)}`;
  }
  return nFormatter(abs);
};

export const TrendCard = ({ metricKey, metric }: TrendCardProps) => {
  const config = TREND_METRIC_CONFIG[metricKey];
  const statType = config?.statType ?? "number";
  const suffix = statType === "percent" ? "%" : undefined;

  return (
    <Card
      variant="borderless"
      title={config?.label ?? metricKey}
      className={classNames("overflow-clip h-full", cardStyles.dashboardCard)}
      cover={
        metric?.history ? (
          <div className="h-16">
            <Sparkline data={metric.history} />
          </div>
        ) : undefined
      }
      coverPosition="bottom"
    >
      {metric ? (
        <>
          <Statistic
            value={formatValue(metric.value, statType)}
            suffix={suffix}
          />
          {metric.diff !== 0 && (
            <Statistic
              trend={metric.diff > 0 ? "up" : "down"}
              value={formatDiff(metric.diff, statType)}
              suffix={suffix}
              prefix={metric.diff > 0 ? "↑" : "↓"}
              className={cardStyles.smallStatistic}
            />
          )}
        </>
      ) : (
        <Skeleton active paragraph={false} />
      )}
    </Card>
  );
};
