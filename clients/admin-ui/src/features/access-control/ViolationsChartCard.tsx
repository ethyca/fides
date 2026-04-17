import {
  antTheme,
  AreaChart,
  BarChart,
  Flex,
  Segmented,
  Statistic,
  Text,
} from "fidesui";
import { useMemo, useState } from "react";

import {
  useGetAccessControlSummaryQuery,
  useGetRequestsTimeseriesQuery,
} from "./access-control.slice";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { getTrendColor, getTrendPrefix } from "./trendUtils";

type ChartMode = "line" | "bar";

const AREA_SERIES = [
  { key: "requests", name: "Total Requests", color: "colorBorder" as const },
  { key: "violations", name: "Violations", color: "colorText" as const },
];

export const ViolationsChartCard = () => {
  const { token } = antTheme.useToken();
  const [mode, setMode] = useState<ChartMode>("line");

  const { filters, timeseriesFilters, onChartIntervalChange } =
    useRequestLogFilterContext();

  const { data: timeseriesData, isLoading: timeseriesLoading } =
    useGetRequestsTimeseriesQuery(timeseriesFilters);

  const { data: summaryData, isLoading: summaryLoading } =
    useGetAccessControlSummaryQuery(filters);

  const loading = timeseriesLoading || summaryLoading;

  const rangeMs = useMemo(() => {
    const start = new Date(timeseriesFilters.start_date).getTime();
    const end = new Date(timeseriesFilters.end_date).getTime();
    return end - start;
  }, [timeseriesFilters.start_date, timeseriesFilters.end_date]);

  const areaChartData = useMemo(
    () =>
      timeseriesData?.items.map((d) => ({
        label: d.label,
        requests: d.requests,
        violations: d.violations,
      })),
    [timeseriesData],
  );

  const barChartData = useMemo(
    () =>
      timeseriesData?.items.map((d) => ({
        label: d.label,
        value: d.violations,
      })),
    [timeseriesData],
  );

  const totalViolations = summaryData?.violations ?? 0;
  const trend = summaryData?.trend ?? 0;

  return (
    <Flex vertical gap={8}>
      <Flex justify="space-between" align="center">
        <Text strong className="text-xs">Violations over time</Text>
        <Segmented
          size="small"
          options={[
            { label: "Line", value: "line" },
            { label: "Bar", value: "bar" },
          ]}
          value={mode}
          onChange={(val) => setMode(val as ChartMode)}
        />
      </Flex>
      <Flex align="baseline" gap="small">
        <Statistic value={totalViolations} />
        <Statistic
          value={Math.abs(trend * 100)}
          precision={1}
          prefix={getTrendPrefix(trend)}
          suffix="% vs last mo"
          valueStyle={{
            color: getTrendColor(trend, token),
            fontSize: token.fontSizeSM,
          }}
        />
      </Flex>
      <div className="h-[120px] w-full">
        {mode === "line" ? (
          <AreaChart
            data={areaChartData}
            series={AREA_SERIES}
            rangeMs={rangeMs}
            onIntervalChange={onChartIntervalChange}
          />
        ) : (
          <BarChart
            data={barChartData}
            size="sm"
            rangeMs={rangeMs}
            onIntervalChange={onChartIntervalChange}
          />
        )}
      </div>
    </Flex>
  );
};
