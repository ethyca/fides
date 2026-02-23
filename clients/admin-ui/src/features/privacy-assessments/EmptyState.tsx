import { Avatar, Button, Flex, Icons, Text, Typography } from "fidesui";
import NextLink from "next/link";

import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";

const { Title } = Typography;

export const EmptyState = () => {
  return (
    <Flex vertical gap="large" align="center" className="mt-20 text-center">
      <Avatar
        shape="square"
        variant="outlined"
        size={64}
        icon={<Icons.Document size={32} />}
      />
      <div>
        <Title level={4}>No assessments run yet</Title>
        <div className="max-w-md">
          <Text type="secondary">
            Run assessments to evaluate your systems against regulatory
            frameworks and identify compliance gaps.
          </Text>
        </div>
      </div>
      <NextLink href={PRIVACY_ASSESSMENTS_EVALUATE_ROUTE} passHref>
        <Button type="primary" icon={<Icons.Add />}>
          Run assessment
        </Button>
      </NextLink>
    </Flex>
  );
};
