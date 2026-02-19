import { Button, Icons, Text, Typography } from "fidesui";
import NextLink from "next/link";

import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";

const { Title } = Typography;

export const EmptyState = () => {
  return (
    <div className="flex flex-col items-center justify-center px-10 py-20 text-center">
      <div className="mb-6 flex size-16 items-center justify-center rounded-lg bg-gray-100">
        <Icons.Document size={32} className="text-gray-400" />
      </div>
      <Title level={4} className="!mb-2">
        No assessments run yet
      </Title>
      <Text type="secondary" className="mb-6 block max-w-md text-sm">
        Run assessments to evaluate your systems against regulatory frameworks
        and identify compliance gaps.
      </Text>
      <NextLink href={PRIVACY_ASSESSMENTS_EVALUATE_ROUTE} passHref>
        <Button type="primary" icon={<Icons.Add />}>
          Run assessment
        </Button>
      </NextLink>
    </div>
  );
};
