import {
  BarChart,
  Card,
  Flex,
  Statistic,
  Typography,
} from "fidesui";
import { useMemo } from "react";

import type { TimeseriesBucket } from "../types";

const { Text } = Typography;

interface ViolationsBarChartCardProps {
  data: TimeseriesBucket[];
  loading?: boolean;
}

export const ViolationsBarChartCard = ({
  data,
  loading,
}: ViolationsBarChartCardProps) => {
  const chartData = data.map((d) => ({
    label: d.label,
    value: d.violations,
  }));
  const totalViolations = useMemo(
    () => data.reduce((sum, d) => sum + d.violations, 0),
    [data],
  );

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
        <BarChart data={chartData} />
      </div>
    </Card>
  );
};
