import { antTheme, Card, DonutChart, Flex, Statistic, Text } from "fidesui";

import { useGetAccessControlSummaryQuery } from "./access-control.slice";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { getTrendColor, getTrendPrefix } from "./trendUtils";

export const ViolationRateCard = () => {
  const { token } = antTheme.useToken();
  const { filters } = useRequestLogFilterContext();

  const { data, isLoading } = useGetAccessControlSummaryQuery(filters);

  const violations = data?.violations ?? 0;
  const totalRequests = data?.total_requests ?? 0;
  const trend = data?.trend ?? 0;

  const ratePercent =
    totalRequests > 0 ? (violations / totalRequests) * 100 : 0;
  const rate = ratePercent > 0 ? ratePercent.toFixed(1) : "0";

  return (
    <Card
      loading={isLoading}
      title={<Text strong>Violation rate</Text>}
      className="flex h-full flex-col"
      classNames={{ body: "flex flex-1 flex-col" }}
    >
      <Flex vertical gap={16} className="flex-1">
        <Flex align="center" gap={16}>
          <div className="size-[100px] shrink-0">
            <DonutChart
              segments={[
                {
                  value: violations,
                  color: "colorText",
                  name: "Violations",
                },
                {
                  value: Math.max(0, totalRequests - violations),
                  color: "colorBorderSecondary",
                  name: "Clean",
                },
              ]}
              centerLabel={
                <Text strong className="text-lg">
                  {rate}%
                </Text>
              }
            />
          </div>
          <Flex vertical gap={2}>
            <Text strong>Violations</Text>
            <Text type="secondary">
              {violations.toLocaleString()} of {totalRequests.toLocaleString()}
            </Text>
            <Statistic
              value={Math.abs(trend * 100)}
              precision={1}
              prefix={getTrendPrefix(trend)}
              suffix="% vs last mo"
              styles={{
                content: {
                  color: getTrendColor(trend, token),
                  fontSize: token.fontSizeSM,
                },
              }}
            />
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};
