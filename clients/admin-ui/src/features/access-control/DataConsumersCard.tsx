import { Card, Divider, Flex, Typography } from "fidesui";

import { MOCK_DATA_CONSUMERS } from "./mock-data";

const { Text } = Typography;

const DataConsumersCard = () => {
  return (
    <Card variant="outlined" className="h-full">
      <Flex justify="space-between" align="flex-start" className="mb-5">
        <Text type="secondary" className="text-xs font-semibold">
          Data consumers
        </Text>
        <Text type="secondary" className="text-xs">
          4 active
        </Text>
      </Flex>

      <div>
        <Flex justify="space-between" className="mb-1 px-1">
          <Text type="secondary" className="text-xs">
            Consumer
          </Text>
          <Flex gap="large">
            <Text type="secondary" className="w-12 text-right text-xs">
              Reqs
            </Text>
            <Text type="secondary" className="w-12 text-right text-xs">
              Viol
            </Text>
          </Flex>
        </Flex>
        <Divider className="!my-1" />
        {MOCK_DATA_CONSUMERS.map((consumer, index) => (
          <div key={consumer.name}>
            <Flex
              justify="space-between"
              align="center"
              className="px-1 py-1.5"
            >
              <Text className="text-sm">{consumer.name}</Text>
              <Flex gap="large">
                <Text className="w-12 text-right text-sm">
                  {consumer.requests}
                </Text>
                <Text
                  type={consumer.violations > 0 ? "danger" : "success"}
                  className="w-12 text-right text-sm font-medium"
                >
                  {consumer.violations}
                </Text>
              </Flex>
            </Flex>
            {index < MOCK_DATA_CONSUMERS.length - 1 && (
              <Divider className="!my-0" />
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default DataConsumersCard;
