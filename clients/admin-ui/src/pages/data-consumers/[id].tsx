import { Card, Flex, Typography, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import ConsumerSummaryBanner from "~/features/data-consumers/ConsumerSummaryBanner";
import DataConsumerForm, {
  DataConsumerFormValues,
} from "~/features/data-consumers/DataConsumerForm";
import { MOCK_DATA_CONSUMERS } from "~/features/data-consumers/mockData";

const EditDataConsumerPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const { id } = router.query;

  const consumer = MOCK_DATA_CONSUMERS.find((c) => c.id === id);

  if (id && !consumer) {
    return (
      <FixedLayout title="Data consumer">
        <PageHeader
          heading="Data consumers"
          breadcrumbItems={[
            { title: "All data consumers", href: DATA_CONSUMERS_ROUTE },
            { title: "Not found" },
          ]}
        />
        <Typography.Text>Consumer not found.</Typography.Text>
      </FixedLayout>
    );
  }

  const handleSubmit = (values: DataConsumerFormValues) => {
    message.success(`Data consumer "${values.name}" updated successfully`);
    router.push(DATA_CONSUMERS_ROUTE);
  };

  return (
    <FixedLayout title={consumer?.name ?? "Data consumer"}>
      <PageHeader
        heading="Data consumers"
        breadcrumbItems={[
          { title: "All data consumers", href: DATA_CONSUMERS_ROUTE },
          { title: consumer?.name ?? "Data consumer" },
        ]}
      />
      <Flex vertical gap="middle">
        {consumer && <ConsumerSummaryBanner consumer={consumer} />}
        <Card size="small" title="Configuration">
          <DataConsumerForm consumer={consumer} onSubmit={handleSubmit} />
        </Card>
      </Flex>
    </FixedLayout>
  );
};

export default EditDataConsumerPage;
