import { antTheme, Card, Flex, Progress, Statistic, Text } from "fidesui";

interface ViolationRateCardProps {
  violations: number;
  totalRequests: number;
  loading?: boolean;
}

const ViolationRateCard = ({
  violations,
  totalRequests,
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
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
      styles={{ body: { flex: 1, display: "flex", flexDirection: "column" } }}
    >
      <Flex vertical gap={12} style={{ marginTop: "auto" }}>
        <Statistic
          value={`${rate}%`}
          valueStyle={{ fontSize: token.fontSizeHeading2 }}
        />
        <Flex justify="space-between">
          <Text type="secondary">Violations</Text>
          <Text strong>{violations.toLocaleString()}</Text>
        </Flex>
        <Flex justify="space-between">
          <Text type="secondary">Total requests</Text>
          <Text strong>{totalRequests.toLocaleString()}</Text>
        </Flex>
        <Progress
          percent={ratePercent}
          showInfo={false}
          strokeColor={token.colorText}
          trailColor={token.colorBorderSecondary}
          size={["100%", 8]}
        />
      </Flex>
    </Card>
  );
};

export default ViolationRateCard;
