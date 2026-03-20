import { antTheme, AreaChart, Card, Statistic, Text } from "fidesui";
import { useMemo } from "react";

import type { TimeseriesBucket } from "../types";

const SERIES = [
  { key: "requests", name: "Total Requests", color: "colorBorder" as const },
  { key: "violations", name: "Violations", color: "colorText" as const },
];

interface ViolationsOverTimeCardProps {
  data: TimeseriesBucket[];
  totalViolations: number;
  trend: number;
  loading?: boolean;
}

export const ViolationsOverTimeCard = ({
  data,
  totalViolations,
  trend,
  loading,
}: ViolationsOverTimeCardProps) => {
  const { token } = antTheme.useToken();

  const chartData = useMemo(
    () =>
      data.map((d) => ({
        label: d.label,
        requests: d.requests,
        violations: d.violations,
      })),
    [data],
  );

  return (
    <Card
      loading={loading}
      title={<Text strong>Violations over time</Text>}
      extra={
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
      }
      className="flex h-full flex-col text-clip"
      cover={
        <div className="h-[200px] w-full">
          <AreaChart data={chartData} series={SERIES} />
        </div>
      }
      styles={{
        cover: { padding: "0 12px 12px" },
      }}
      coverPosition="bottom"
    >
      <Statistic
        value={totalViolations}
        valueStyle={{
          color: token.colorError,
          fontSize: token.fontSizeHeading2,
        }}
      />
    </Card>
  );
};
