import { Card, Divider, Flex, Text } from "fidesui";

import {
  MOCK_GAP_CARDS,
  MOCK_UNRESOLVED_IDENTITIES,
  MOCK_VIOLATION_CARDS,
} from "./mockData";

export const PendingActionsCard = () => {
  const unresolvedCount = MOCK_UNRESOLVED_IDENTITIES.length;
  const violationCount = MOCK_VIOLATION_CARDS.length;
  const gapCount = MOCK_GAP_CARDS.length;
  const total = unresolvedCount + violationCount + gapCount;

  const rows: { label: string; count: number; danger?: boolean }[] = [
    { label: "Unresolved identities", count: unresolvedCount, danger: true },
    { label: "Policy violations", count: violationCount },
    { label: "Policy gaps", count: gapCount },
  ];

  return (
    <Card title={<Text strong>Pending actions</Text>} className="h-full">
      <Flex vertical gap={10}>
        {rows.map(({ label, count, danger }) => (
          <Flex key={label} justify="space-between" align="center">
            <Text type="secondary" className="text-xs">
              {label}
            </Text>
            <Text
              strong
              type={danger && count > 0 ? "danger" : undefined}
              className="text-sm"
            >
              {count}
            </Text>
          </Flex>
        ))}
        <Divider className="!my-1" />
        <Flex justify="space-between" align="center">
          <Text type="secondary" className="text-xs">
            Total
          </Text>
          <Text strong className="text-sm">
            {total}
          </Text>
        </Flex>
      </Flex>
    </Card>
  );
};
