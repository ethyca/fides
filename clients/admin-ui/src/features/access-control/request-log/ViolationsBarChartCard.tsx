import {
  BarChart,
  Card,
  deriveInterval,
  Flex,
  Statistic,
  Typography,
} from "fidesui";

import type { DataConsumerRequestPoint } from "../types";

const { Text } = Typography;

interface ViolationsBarChartCardProps {
  data: DataConsumerRequestPoint[];
  totalViolations: number;
  loading?: boolean;
}

export const ViolationsBarChartCard = ({
  data,
  totalViolations,
  loading,
}: ViolationsBarChartCardProps) => {
  const intervalMs = deriveInterval(data);
  const chartData = data.map((d) => ({
    label: d.timestamp,
    value: d.violations,
  }));

  return (
    <Card loading={loading}>
      <div className="mb-2">
        <Text type="secondary" className="text-xs font-semibold">
          Violations over time
        </Text>
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
        <BarChart data={chartData} intervalMs={intervalMs} />
      </div>
    </Card>
  );
};
