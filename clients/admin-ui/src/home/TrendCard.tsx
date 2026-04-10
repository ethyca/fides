import { format, subDays } from "date-fns";
import {
  antTheme,
  Card,
  Flex,
  Icons,
  Skeleton,
  Sparkline,
  Statistic,
  Text,
  Tooltip,
} from "fidesui";
import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/types";

/** Generate short date labels (e.g. "Mar 11") spaced evenly across a number of days. */
const buildDateLabels = (pointCount: number, days: number): string[] => {
  const now = new Date();
  return Array.from({ length: pointCount }, (_, i) => {
    const daysAgo = days - (days * i) / (pointCount - 1 || 1);
    return format(subDays(now, daysAgo), "MMM d");
  });
};

type StatType = "number" | "percent";

const TREND_METRIC_CONFIG = {
  gps_score: {
    label: "Governance posture",
    statType: "number",
    description: "Overall governance posture score across all dimensions",
  },
  dsr_volume: {
    label: "DSR volume",
    statType: "number",
    description: "Total data subject requests received in this period",
  },
  system_coverage: {
    label: "System coverage",
    statType: "percent",
    description:
      "Percentage of systems with at least one data classification applied",
  },
  classification_health: {
    label: "Classification health",
    statType: "percent",
    description:
      "Percentage of classified data fields that are accurate and up to date",
  },
} satisfies Record<
  string,
  { label: string; statType: StatType; description: string }
>;

export type TrendMetricKey = keyof typeof TREND_METRIC_CONFIG;

export const TREND_METRIC_KEYS = Object.keys(
  TREND_METRIC_CONFIG,
) as TrendMetricKey[];

interface TrendCardProps {
  metricKey: TrendMetricKey;
  metric: TrendMetric | undefined;
  isLoading: boolean;
  periodLabel?: string;
}

const formatMetric = (value: number, statType: StatType) => {
  if (statType === "percent") {
    return `${Math.round(value)}`;
  }
  return nFormatter(value);
};

export const TrendCard = ({
  metricKey,
  metric,
  isLoading,
  periodLabel = "Last 30 days",
}: TrendCardProps) => {
  const { token } = antTheme.useToken();
  const config = TREND_METRIC_CONFIG[metricKey];
  const statType = config?.statType ?? "number";
  const suffix = statType === "percent" ? "%" : undefined;
  const formattedDiff = metric
    ? formatMetric(Math.abs(metric.diff), statType)
    : undefined;

  const xAxisLabels = useMemo(
    () =>
      metric?.history ? buildDateLabels(metric.history.length, 30) : undefined,
    [metric?.history],
  );

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
      title={
        <Tooltip title={config?.description}>
          <span>{config?.label ?? metricKey}</span>
        </Tooltip>
      }
      className="h-full text-clip"
      cover={
        !isLoading ? (
          <div className="h-20">
            <Sparkline
              data={metric?.history}
              xAxisLabels={xAxisLabels}
            />
          </div>
        ) : undefined
      }
      coverPosition="bottom"
    >
      {renderStats()}
    </Card>
  );
};
