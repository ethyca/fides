import { Card, Divider, Flex, Progress, Typography } from "fidesui";

import {
  MOCK_TOP_VIOLATED_POLICIES,
  MOCK_TOTAL_REQUESTS,
  MOCK_TOTAL_VIOLATIONS,
  MOCK_VIOLATION_RATE,
  MOCK_VIOLATION_RATE_TREND,
} from "./mock-data";

const { Text } = Typography;

const formatPercent = () => `${MOCK_VIOLATION_RATE}%`;

const ViolationRateCard = () => {
  return (
    <Card variant="outlined" className="h-full">
      <Flex justify="space-between" align="flex-start" className="mb-4">
        <Text type="secondary" className="text-xs font-semibold">
          Violation rate
        </Text>
        <Text type="secondary" className="text-xs">
          15 policies
        </Text>
      </Flex>

      <Flex align="center" gap="middle" className="mt-4">
        <Progress
          type="circle"
          percent={MOCK_VIOLATION_RATE}
          size={80}
          strokeColor="#1a1a1a"
          trailColor="#e3e0d9"
          format={formatPercent}
        />
        <div>
          <Text strong>Violations</Text>
          <div>
            <Text type="secondary" className="text-sm">
              {MOCK_TOTAL_VIOLATIONS} of {MOCK_TOTAL_REQUESTS}
            </Text>
          </div>
          <Text type="success" className="text-xs font-medium">
            {MOCK_VIOLATION_RATE_TREND} vs last mo
          </Text>
        </div>
      </Flex>

      <Divider className="!my-3" />

      <div>
        <Text
          className="mb-2 block text-xs font-semibold"
          style={{ color: "#2b2e35" }}
        >
          Top violated policies
        </Text>
        <Text type="secondary" className="text-xs">
          {MOCK_TOP_VIOLATED_POLICIES.map((p, i) => (
            <span key={p.name}>
              {p.name} {p.count}
              {i < MOCK_TOP_VIOLATED_POLICIES.length - 1 && " · "}
            </span>
          ))}
        </Text>
      </div>
    </Card>
  );
};

export default ViolationRateCard;
