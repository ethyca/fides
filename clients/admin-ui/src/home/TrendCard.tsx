import { format, subDays } from "date-fns";
import type { BarChartDataPoint } from "fidesui";
import {
  antTheme,
  BarChart,
  Card,
  Flex,
  Icons,
  Skeleton,
  Sparkline,
  Statistic,
  Text,
  Tooltip,
} from "fidesui";
import { useCallback, useMemo } from "react";

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

type ChartType = "sparkline" | "bar";

const TREND_METRIC_CONFIG = {
  gps_score: {
    label: "Governance posture",
    statType: "number",
    chartType: "sparkline",
    description: "Overall governance posture score across all dimensions",
  },
  dsr_volume: {
    label: "DSR volume",
    statType: "number",
    chartType: "bar",
    description: "Total data subject requests received in this period",
  },
  system_coverage: {
    label: "System coverage",
    statType: "percent",
    chartType: "sparkline",
    description:
      "Percentage of systems with at least one data classification applied",
  },
  classification_health: {
    label: "Classification health",
    statType: "percent",
    chartType: "sparkline",
    description:
      "Percentage of classified data fields that are accurate and up to date",
  },
} satisfies Record<
  string,
  {
    label: string;
    statType: StatType;
    chartType: ChartType;
    description: string;
  }
>;

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

  const chartType = config?.chartType ?? "sparkline";

  const xAxisLabels = useMemo(
    () =>
      metric?.history ? buildDateLabels(metric.history.length, 30) : undefined,
    [metric?.history],
  );

  const barData = useMemo<BarChartDataPoint[] | undefined>(
    () =>
      metric?.history && xAxisLabels
        ? metric.history.map((v, i) => ({
            label: xAxisLabels[i],
            value: v,
          }))
        : undefined,
    [metric?.history, xAxisLabels],
  );

  const renderTooltipContent = useCallback(
    (value: number, label: string) => (
      <span>
        {label && <>{label}: </>}
        {formatMetric(value, statType)}
        {suffix}
      </span>
    ),
    [statType, suffix],
  );

  const renderStats = () => {
    if (isLoading) {
      return <Skeleton active paragraph={false} />;
    }
    if (!metric) {
      return (
        <Statistic
          value="—"
          styles={{ content: { color: token.colorTextDisabled } }}
        />
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
        <Tooltip title={config?.description} placement="bottom">
          <Flex
            align="center"
            gap={4}
            style={{ cursor: "pointer", display: "inline-flex" }}
          >
            <Text>{config?.label ?? metricKey}</Text>
            <Icons.Help size={14} className="opacity-30" />
          </Flex>
        </Tooltip>
      }
      className="h-full text-clip [&_.ant-card-body]:pt-0"
      cover={
        !isLoading ? (
          <div className="h-20">
            {chartType === "bar" ? (
              <div className="h-full px-2">
                <BarChart
                  color="colorTextQuaternary"
                  data={barData}
                  size="sm"
                  showTooltip={false}
                  simpleXAxis
                  tooltipContent={renderTooltipContent}
                />
              </div>
            ) : (
              <Sparkline
                data={metric?.history}
                xAxisLabels={xAxisLabels}
                tooltipContent={renderTooltipContent}
              />
            )}
          </div>
        ) : undefined
      }
      coverPosition="bottom"
    >
      {renderStats()}
    </Card>
  );
};
