import { Card, Flex, Statistic, Typography } from "fidesui";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  MOCK_HOURLY_VIOLATIONS,
  MOCK_TOTAL_REQUEST_LOG_VIOLATIONS,
} from "./mock-data";

const SANDSTONE_STROKE = "#cecac2";
const SANDSTONE_BG = "#e3e0d9";

const { Text } = Typography;

const RequestLogChart = () => {
  return (
    <Card className="mb-6">
      <div className="mb-2">
        <Text type="secondary" className="text-xs font-semibold">
          Violations over time
        </Text>
        <Flex align="baseline" gap="small" className="mt-1">
          <Statistic
            value={MOCK_TOTAL_REQUEST_LOG_VIOLATIONS}
            valueStyle={{ fontSize: 28, fontWeight: 700 }}
          />
          <Text type="secondary" className="text-sm">
            Total violations
          </Text>
        </Flex>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={MOCK_HOURLY_VIOLATIONS}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            barCategoryGap="8%"
          >
            <defs>
              <linearGradient
                id="barSandstoneGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={SANDSTONE_STROKE}
                  stopOpacity={1}
                />
                <stop
                  offset="100%"
                  stopColor={SANDSTONE_BG}
                  stopOpacity={0.6}
                />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="label"
              tick={{ fontSize: 9 }}
              interval={19}
              axisLine
              tickLine={false}
            />
            <YAxis hide />
            <Tooltip
              cursor={{ fill: "rgba(0,0,0,0.04)" }}
              contentStyle={{
                fontSize: 12,
                borderRadius: 6,
                border: "1px solid #e3e0d9",
              }}
              labelFormatter={(label) => label || ""}
              formatter={(value: number) => [value, "Violations"]}
            />
            <Bar
              dataKey="violations"
              fill="url(#barSandstoneGradient)"
              radius={[1, 1, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

export default RequestLogChart;
