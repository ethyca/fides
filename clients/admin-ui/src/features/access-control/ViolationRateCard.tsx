import { Card, DonutChart, Flex, Statistic, Text } from "fidesui";
import { theme as antTheme } from "antd";

interface ViolationRateCardProps {
  violations: number;
  totalRequests: number;
  trend: number;
  loading?: boolean;
}

const getTrendColor = (trend: number, token: ReturnType<typeof antTheme.useToken>["token"]) => {
  if (trend < 0) return token.colorSuccess;
  if (trend > 0) return token.colorErrorText;
  return token.colorTextSecondary;
};

export const ViolationRateCard = ({
  violations,
  totalRequests,
  trend,
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
      className="flex h-full flex-col"
      classNames={{ body: "flex flex-1 flex-col" }}
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
              prefix={trend < 0 ? "-" : trend > 0 ? "+" : ""}
              suffix="% vs last mo"
              valueStyle={{
                color: getTrendColor(trend, token),
                fontSize: token.fontSizeSM,
              }}
            />
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};
