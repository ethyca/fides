import { antTheme, Card, DonutChart, Flex, Statistic, Text } from "fidesui";

interface ViolationRateCardProps {
  violations: number;
  totalRequests: number;
  trend: number;
  totalPolicies: number;
  loading?: boolean;
}

export const ViolationRateCard = ({
  violations,
  totalRequests,
  trend,
  totalPolicies,
  loading,
}: ViolationRateCardProps) => {
  const { token } = antTheme.useToken();
  const ratePercent =
    totalRequests > 0 ? (violations / totalRequests) * 100 : 0;
  const rate = ratePercent > 0 ? ratePercent.toFixed(1) : "0";

  return (
    <Card
      loading={loading}
      title={<Text strong>Violation rate</Text>}
      extra={
        <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>
          {totalPolicies} policies
        </Text>
      }
      className="flex h-full flex-col"
      styles={{ body: { flex: 1, display: "flex", flexDirection: "column" } }}
    >
      <Flex vertical gap={16} className="flex-1">
        <Flex align="center" gap={16}>
          <div className="h-[100px] w-[100px] shrink-0">
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
                <Text strong style={{ fontSize: token.fontSizeLG }}>
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
              prefix={trend < 0 ? "-" : trend > 0 ? "+" : ""}
              suffix="% vs last mo"
              valueStyle={{
                color:
                  trend < 0
                    ? token.colorSuccess
                    : trend > 0
                      ? token.colorError
                      : token.colorTextSecondary,
                fontSize: token.fontSizeSM,
              }}
            />
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};
