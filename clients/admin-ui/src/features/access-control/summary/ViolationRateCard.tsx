import { antTheme, Card, Flex, Text } from "fidesui";
// eslint-disable-next-line import/no-extraneous-dependencies
import { Cell, Pie, PieChart } from "recharts";

import type { TopPolicyViolation } from "../types";

const DONUT_SIZE = 100;
const INNER_RADIUS = 35;
const OUTER_RADIUS = 48;

const formatTrend = (trend: number) => {
  const pct = Math.abs(trend * 100).toFixed(1);
  const sign = trend <= 0 ? "-" : "+";
  return `${sign}${pct}% vs last mo`;
};

interface ViolationRateCardProps {
  violations: number;
  totalRequests: number;
  trend: number;
  topPolicies: TopPolicyViolation[];
  totalPolicies: number;
  loading?: boolean;
}

export const ViolationRateCard = ({
  violations,
  totalRequests,
  trend,
  topPolicies,
  totalPolicies,
  loading,
}: ViolationRateCardProps) => {
  const { token } = antTheme.useToken();
  const ratePercent =
    totalRequests > 0 ? (violations / totalRequests) * 100 : 0;
  const rate = ratePercent > 0 ? ratePercent.toFixed(1) : "0";

  const donutData = [
    { name: "Violations", value: violations },
    { name: "Clean", value: Math.max(0, totalRequests - violations) },
  ];

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
          <div
            className="relative shrink-0"
            style={{ width: DONUT_SIZE, height: DONUT_SIZE }}
          >
            <PieChart width={DONUT_SIZE} height={DONUT_SIZE}>
              <Pie
                data={donutData}
                cx={DONUT_SIZE / 2 - 1}
                cy={DONUT_SIZE / 2 - 1}
                innerRadius={INNER_RADIUS}
                outerRadius={OUTER_RADIUS}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
                stroke="none"
              >
                <Cell fill={token.colorText} />
                <Cell fill={token.colorBorderSecondary} />
              </Pie>
            </PieChart>
            <div className="absolute inset-0 flex items-center justify-center">
              <Text strong style={{ fontSize: token.fontSizeLG }}>
                {rate}%
              </Text>
            </div>
          </div>
          <Flex vertical gap={2}>
            <Text strong>Violations</Text>
            <Text type="secondary">
              {violations.toLocaleString()} of {totalRequests.toLocaleString()}
            </Text>
            <Text
              style={{
                color: trend <= 0 ? token.colorSuccess : token.colorError,
                fontSize: token.fontSizeSM,
              }}
            >
              {formatTrend(trend)}
            </Text>
          </Flex>
        </Flex>

        <div>
          <Text strong>Top violated policies</Text>
          <div className="mt-1">
            <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>
              {topPolicies.map((p) => `${p.name} ${p.count}`).join(" \u00b7 ")}
            </Text>
          </div>
        </div>
      </Flex>
    </Card>
  );
};
