import classNames from "classnames";
import { Card, Skeleton, Sparkline, Statistic } from "fidesui";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/types";

import cardStyles from "./dashboard-card.module.scss";

type StatType = "number" | "percent";

const TREND_METRIC_CONFIG = {
  gps_score: { label: "GPS Score", statType: "number" as StatType },
  dsr_volume: { label: "DSR Volume", statType: "number" as StatType },
  system_coverage: {
    label: "System Coverage",
    statType: "percent" as StatType,
  },
  classification_health: {
    label: "Classification Health",
    statType: "percent" as StatType,
  },
};

export type TrendMetricKey = keyof typeof TREND_METRIC_CONFIG;

export const TREND_METRIC_KEYS = Object.keys(
  TREND_METRIC_CONFIG,
) as TrendMetricKey[];

interface TrendCardProps {
  metricKey: TrendMetricKey;
  metric: TrendMetric | undefined;
}

const formatMetric = (value: number, statType: StatType) => {
  if (statType === "percent") {
    return `${Math.round(value)}`;
  }
  return nFormatter(value);
};

export const TrendCard = ({ metricKey, metric }: TrendCardProps) => {
  const config = TREND_METRIC_CONFIG[metricKey];
  const statType = config?.statType ?? "number";
  const suffix = statType === "percent" ? "%" : undefined;
  const formattedDiff = metric
    ? formatMetric(Math.abs(metric.diff), statType)
    : undefined;

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
            value={formatMetric(metric.value, statType)}
            suffix={suffix}
          />
          {metric.diff !== 0 && formattedDiff !== "0" && (
            <Statistic
              trend={metric.diff > 0 ? "up" : "down"}
              value={formattedDiff}
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
