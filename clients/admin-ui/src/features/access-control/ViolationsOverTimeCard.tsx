import { Card, Flex, Statistic, Typography } from "fidesui";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import {
  MOCK_DAILY_VIOLATIONS,
  MOCK_TOTAL_VIOLATIONS,
  MOCK_VIOLATION_TREND,
} from "./mock-data";

const { Text } = Typography;

const SPARKLINE_STROKE = "#a8aaad";
const SANDSTONE_BG = "#e3e0d9";

const SparklineChart = () => {
  return (
    <div>
      <div className="h-24">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={MOCK_DAILY_VIOLATIONS}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          >
            <defs>
              <linearGradient
                id="sandstoneGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={SANDSTONE_BG} stopOpacity={1} />
                <stop offset="100%" stopColor={SANDSTONE_BG} stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="day"
              tick={{ fontSize: 9 }}
              interval={6}
              axisLine={false}
              tickLine={false}
            />
            <YAxis domain={[0, "dataMax"]} hide />
            <Area
              type="basis"
              dataKey="violations"
              stroke={SPARKLINE_STROKE}
              strokeWidth={2}
              fill="url(#sandstoneGradient)"
              dot={false}
              activeDot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const ViolationsOverTimeCard = () => {
  return (
    <Card
      variant="outlined"
      coverPosition="bottom"
      cover={<SparklineChart />}
      className="h-full overflow-hidden"
    >
      <Flex justify="space-between" align="flex-start">
        <Statistic
          title="Violations over time"
          value={MOCK_TOTAL_VIOLATIONS}
          valueStyle={{ color: "#d9534f" }}
        />
        <Text type="success" className="text-xs font-medium">
          {MOCK_VIOLATION_TREND} vs last mo
        </Text>
      </Flex>
    </Card>
  );
};

export default ViolationsOverTimeCard;
