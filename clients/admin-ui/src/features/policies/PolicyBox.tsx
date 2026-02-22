import { Card, Flex, Typography } from "fidesui";

import { PolicyResponse } from "~/types/api";

const { Title, Text } = Typography;

interface PolicyBoxProps {
  policy: PolicyResponse;
}

const PolicyBox = ({ policy }: PolicyBoxProps) => {
  return (
    <Card data-testid="policy-box">
      <Flex vertical gap="small">
        <Flex align="center" gap="small">
          <Title level={5}>{policy.name}</Title>
        </Flex>
        <Text type="secondary" code>
          {policy.key}
        </Text>
      </Flex>
    </Card>
  );
};

export default PolicyBox;
