import {
  LineChart,
  BarChart,
  Card,
  Flex,
  Segmented,
  Statistic,
  Text,
} from "fidesui";
import { theme as antTheme } from "antd";
import { useMemo, useState } from "react";

import {
  useGetAccessControlSummaryQuery,
  useGetRequestsTimeseriesQuery,
} from "./access-control.slice";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";

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
    useGetAccessControlSummaryQuery({
      start_date: filters.start_date,
      end_date: filters.end_date,
    });

  const loading = timeseriesLoading || summaryLoading;

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

  const getTrendPrefix = () => {
    if (trend < 0) return "-";
    if (trend > 0) return "+";
    return "";
  };

  const getTrendColor = () => {
    if (trend < 0) return token.colorSuccess;
    if (trend > 0) return token.colorError;
    return token.colorTextSecondary;
  };

  return (
    <Card
      loading={loading}
      title={<Text strong>Violations over time</Text>}
      extra={
        <Segmented
          size="small"
          options={[
            { label: "Line", value: "line" },
            { label: "Bar", value: "bar" },
          ]}
          value={mode}
          onChange={(val) => setMode(val as ChartMode)}
        />
      }
      className="flex h-full flex-col text-clip"
      cover={
        <div className="h-[120px] w-full">
          {mode === "line" ? (
            <LineChart data={areaChartData} series={AREA_SERIES} />
          ) : (
            <BarChart
              data={barChartData}
              size="lg"
              onIntervalChange={onChartIntervalChange}
            />
          )}
        </div>
      }
      classNames={{
        cover: "px-3 pb-3",
        body: "!pt-0",
      }}
      coverPosition="bottom"
    >
      <Flex align="baseline" gap="small">
        <Statistic value={totalViolations} />
        <Statistic
          value={Math.abs(trend * 100)}
          precision={1}
          prefix={getTrendPrefix()}
          suffix="% vs last mo"
          valueStyle={{
            color: getTrendColor(),
            fontSize: token.fontSizeSM,
          }}
        />
      </Flex>
    </Card>
  );
};
