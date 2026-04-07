import { Button, Flex, Form, Input, Select, Spin } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import { useGetAllDataPurposesQuery } from "~/features/data-purposes/data-purpose.slice";

import { CONSUMER_TYPE_OPTIONS } from "./constants";
import { DataConsumer } from "./data-consumer.slice";

export interface DataConsumerFormValues {
  name: string;
  type: string;
  contact_email: string;
  description: string;
  tags: string[];
  purposeFidesKeys: string[];
}

interface DataConsumerFormProps {
  consumer?: DataConsumer;
  handleSubmit: (values: DataConsumerFormValues) => Promise<void>;
}

const DataConsumerForm = ({
  consumer,
  handleSubmit,
}: DataConsumerFormProps) => {
  const [form] = Form.useForm<DataConsumerFormValues>();
  const router = useRouter();

  const { data: purposesData, isLoading: purposesLoading } =
    useGetAllDataPurposesQuery({ size: 200 });

  const purposeOptions = useMemo(
    () =>
      (purposesData?.items ?? []).map((p) => ({
        value: p.fides_key,
        label: p.name || p.fides_key,
      })),
    [purposesData],
  );

  const initialValues = useMemo<DataConsumerFormValues>(
    () => ({
      name: consumer?.name ?? "",
      type: consumer?.type ?? "",
      contact_email: consumer?.contact_email ?? "",
      description: consumer?.description ?? "",
      tags: consumer?.tags ?? [],
      purposeFidesKeys: consumer?.purpose_fides_keys ?? [],
    }),
    [consumer],
  );

  const handleCancel = useCallback(() => {
    router.push(DATA_CONSUMERS_ROUTE);
  }, [router]);

  if (purposesLoading) {
    return <Spin />;
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={initialValues}
      key={consumer?.id ?? "create"}
      data-testid="data-consumer-form"
      style={{ maxWidth: 720 }}
    >
      <Form.Item
        name="name"
        label="Name"
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input
          placeholder="Enter consumer name"
          data-testid="data-consumer-name-input"
        />
      </Form.Item>

      <Form.Item
        name="type"
        label="Type"
        rules={[{ required: true, message: "Type is required" }]}
        tooltip="The type of data consumer (service, application, group, or user)"
      >
        <Select
          placeholder="Select consumer type"
          options={CONSUMER_TYPE_OPTIONS}
          aria-label="Type"
          data-testid="data-consumer-type-select"
        />
      </Form.Item>

      <Form.Item
        name="contact_email"
        label="Contact email"
        tooltip="The email address used to identify this consumer in query logs"
      >
        <Input
          placeholder="Enter contact email"
          data-testid="data-consumer-contact-input"
        />
      </Form.Item>

      <Form.Item
        name="purposeFidesKeys"
        label="Assigned purposes"
        tooltip="Which data purposes is this consumer authorized for?"
      >
        <Select
          mode="multiple"
          placeholder="Select purposes"
          options={purposeOptions}
          aria-label="Assigned purposes"
          data-testid="data-consumer-purposes-select"
        />
      </Form.Item>

      <Form.Item
        name="description"
        label="Description"
        tooltip="An optional description of this data consumer"
      >
        <Input.TextArea
          placeholder="Enter a description"
          rows={3}
          data-testid="data-consumer-description-input"
        />
      </Form.Item>

      <Form.Item
        name="tags"
        label="Tags"
        tooltip="Optional tags for organizing consumers"
      >
        <Select
          mode="tags"
          placeholder="Add tags"
          aria-label="Tags"
          data-testid="data-consumer-tags-select"
        />
      </Form.Item>

      <Flex justify="space-between" className="pt-4">
        <Button onClick={handleCancel} data-testid="cancel-button">
          Cancel
        </Button>
        <Button
          type="primary"
          htmlType="submit"
          data-testid="save-data-consumer-button"
        >
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default DataConsumerForm;
