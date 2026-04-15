import { Button, Flex, Tabs, Tag, Text, Title, Tooltip, useMessage } from "fidesui";
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

const MAX_VISIBLE_PURPOSES = 4;

interface LabeledTagsProps {
  label: string;
  values: string[];
  maxVisible?: number;
}

const LabeledTags = ({ label, values, maxVisible }: LabeledTagsProps) => {
  if (values.length === 0) return null;
  const visible = maxVisible ? values.slice(0, maxVisible) : values;
  const remaining = maxVisible ? values.length - maxVisible : 0;
  const hiddenValues = remaining > 0 ? values.slice(maxVisible) : [];

  return (
    <Flex align="center" gap="small" wrap>
      <Text type="secondary" className="text-xs font-medium">
        {label}
      </Text>
      {visible.map((v) => (
        <Tag key={v} bordered={false}>
          {v}
        </Tag>
      ))}
      {remaining > 0 && (
        <Tooltip title={hiddenValues.join(", ")}>
          <Tag bordered={false} className="cursor-default">
            +{remaining} more
          </Tag>
        </Tooltip>
      )}
    </Flex>
  );
};

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
          <Title level={2} style={{ marginBottom: 8 }}>
            {consumer?.name}
          </Title>
          <Flex gap="middle" wrap align="center">
            <LabeledTags
              label="Type"
              values={[
                CONSUMER_TYPE_UI_LABELS[consumer?.type as ConsumerType] ??
                  consumer?.type ??
                  "",
              ]}
            />
            {consumer?.platform && (
              <LabeledTags
                label="Platform"
                values={[
                  PLATFORM_LABELS[consumer.platform] ?? consumer.platform,
                ]}
              />
            )}
            <LabeledTags label="Scope" values={[consumer?.identifier ?? ""]} />
            <LabeledTags
              label="Purposes"
              values={consumer?.purposes ?? []}
              maxVisible={MAX_VISIBLE_PURPOSES}
            />
          </Flex>
        </div>
        <Tabs items={tabItems} defaultActiveKey="overview" />
      </Flex>
    </FixedLayout>
  );
};

export default EditDataConsumerPage;
