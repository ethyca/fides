import { BarChart, Card, Flex, Statistic, Typography } from "fidesui";
import { useMemo } from "react";

import { useGetRequestsTimeseriesQuery } from "../access-control.slice";
import { useRequestLogFilterContext } from "./useRequestLogFilters";

const { Text } = Typography;

export const ViolationsBarChartCard = () => {
  const { timeseriesFilters, onChartIntervalChange } =
    useRequestLogFilterContext();
  const { data, isLoading } = useGetRequestsTimeseriesQuery(timeseriesFilters);

  const chartData = useMemo(
    () => data?.items.map((d) => ({ label: d.label, value: d.violations })),
    [data],
  );

  const totalViolations = useMemo(
    () => data?.items.reduce((sum, d) => sum + d.violations, 0) ?? 0,
    [data],
  );

  return (
    <Card loading={isLoading}>
      <div className="mb-2">
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
        <BarChart
          data={chartData}
          size="lg"
          onIntervalChange={onChartIntervalChange}
        />
      </div>
    </Card>
  );
};
