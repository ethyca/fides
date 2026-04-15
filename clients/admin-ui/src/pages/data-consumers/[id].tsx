import { Button, Flex, Tabs, Tag, Text, Title, useMessage } from "fidesui";
import type { NextPage } from "next";
import Link from "next/link";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import {
  ACCESS_CONTROL_ROUTE,
  DATA_CONSUMERS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  CONSUMER_TYPE_UI_LABELS,
  PLATFORM_LABELS,
} from "~/features/data-consumers/constants";
import ConsumerDetailOverview from "~/features/data-consumers/ConsumerDetailOverview";
import DataConsumerForm, {
  DataConsumerFormValues,
} from "~/features/data-consumers/DataConsumerForm";
import { MOCK_DATA_CONSUMERS } from "~/features/data-consumers/mockData";
import type { ConsumerType } from "~/features/data-consumers/types";

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
        <Text>Consumer not found.</Text>
      </FixedLayout>
    );
  }

  const handleSubmit = (values: DataConsumerFormValues) => {
    message.success(`Data consumer "${values.name}" updated successfully`);
    router.push(DATA_CONSUMERS_ROUTE);
  };

  const tabItems = [
    {
      key: "overview",
      label: (
        <Flex align="center" gap={6}>
          Activity
          {consumer && consumer.findingsCount > 0 && (
            <Tag>{consumer.findingsCount}</Tag>
          )}
        </Flex>
      ),
      children: consumer ? (
        <ConsumerDetailOverview consumer={consumer} />
      ) : null,
    },
    {
      key: "configuration",
      label: "Configuration",
      children: <DataConsumerForm consumer={consumer} onSubmit={handleSubmit} />,
    },
  ];

  return (
    <FixedLayout title={consumer?.name ?? "Data consumer"}>
      <PageHeader
        heading="Data consumers"
        breadcrumbItems={[
          { title: "All data consumers", href: DATA_CONSUMERS_ROUTE },
          { title: consumer?.name ?? "Data consumer" },
        ]}
        rightContent={
          <Link href={ACCESS_CONTROL_ROUTE}>
            <Button type="default">View in access control ↗</Button>
          </Link>
        }
      />
      <Flex vertical gap="middle" className="h-full overflow-y-auto pr-2">
        <div>
          <Title level={2} style={{ marginBottom: 4 }}>
            {consumer?.name}
          </Title>
          <Flex gap="middle" align="center">
            <Text type="secondary">Scope: {consumer?.identifier}</Text>
            <Tag>
              {CONSUMER_TYPE_UI_LABELS[consumer?.type as ConsumerType] ??
                consumer?.type}
            </Tag>
            {consumer?.platform && (
              <Text type="secondary">
                {PLATFORM_LABELS[consumer.platform] ?? consumer.platform}
              </Text>
            )}
          </Flex>
        </div>
        <Tabs items={tabItems} defaultActiveKey="overview" />
      </Flex>
    </FixedLayout>
  );
};

export default EditDataConsumerPage;
