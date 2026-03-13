import { Card, Divider, Flex, Text } from "fidesui";

import type { DataConsumerSummary } from "../types";

interface DataConsumersCardProps {
  data: DataConsumerSummary[];
  loading?: boolean;
}

export const DataConsumersCard = ({
  data,
  loading,
}: DataConsumersCardProps) => (
  <Card loading={loading} title={<Text strong>Top data consumers</Text>}>
    <Flex vertical>
      {data.map((item, index) => (
        <div key={item.name}>
          {index > 0 && <Divider className="my-1" />}
          <Flex justify="space-between" align="center">
            <Text>{item.name}</Text>
            <Flex gap={16}>
              <Text type="secondary">
                {item.requests.toLocaleString()} requests
              </Text>
              <Text type="secondary">
                {item.violations.toLocaleString()} violations
              </Text>
            </Flex>
          </Flex>
        </div>
      ))}
    </Flex>
  </Card>
);
