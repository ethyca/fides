import { Button, Flex, Form, Input, Select } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";

import { CONSUMER_TYPE_UI_OPTIONS, PLATFORM_OPTIONS } from "./constants";
import type { MockDataConsumer } from "./types";

export interface DataConsumerFormValues {
  name: string;
  type: string;
  identifier: string;
  platform: string | null;
  purposes: string[];
  description: string;
}

interface DataConsumerFormProps {
  consumer?: MockDataConsumer;
  onSubmit: (values: DataConsumerFormValues) => void;
}

const MOCK_PURPOSE_OPTIONS = [
  { value: "Campaign targeting", label: "Campaign targeting" },
  { value: "Audience segmentation", label: "Audience segmentation" },
  { value: "Customer support", label: "Customer support" },
  { value: "Ticket resolution", label: "Ticket resolution" },
  { value: "Predictive analytics", label: "Predictive analytics" },
  { value: "Fraud prevention", label: "Fraud prevention" },
  { value: "Transaction monitoring", label: "Transaction monitoring" },
  { value: "Profile unification", label: "Profile unification" },
  { value: "Employee admin", label: "Employee admin" },
  { value: "Payroll processing", label: "Payroll processing" },
  { value: "Product improvement", label: "Product improvement" },
  { value: "Usage analytics", label: "Usage analytics" },
  { value: "Regulatory reporting", label: "Regulatory reporting" },
  { value: "Transactional email", label: "Transactional email" },
  { value: "Marketing email", label: "Marketing email" },
  { value: "Personalization", label: "Personalization" },
  { value: "Analytics", label: "Analytics" },
];

const DataConsumerForm = ({ consumer, onSubmit }: DataConsumerFormProps) => {
  const [form] = Form.useForm<DataConsumerFormValues>();
  const router = useRouter();

  const initialValues = useMemo<DataConsumerFormValues>(
    () => ({
      name: consumer?.name ?? "",
      type: consumer?.type ?? "",
      identifier: consumer?.identifier ?? "",
      platform: consumer?.platform ?? null,
      purposes: consumer?.purposes ?? [],
      description: "",
    }),
    [consumer],
  );

  const handleCancel = useCallback(() => {
    router.push(DATA_CONSUMERS_ROUTE);
  }, [router]);

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onSubmit}
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
        <Input placeholder="Enter consumer name" />
      </Form.Item>

      <Form.Item
        name="type"
        label="Type"
        rules={[{ required: true, message: "Type is required" }]}
        tooltip="The type of data consumer"
      >
        <Select
          placeholder="Select consumer type"
          options={CONSUMER_TYPE_UI_OPTIONS}
          aria-label="Type"
        />
      </Form.Item>

      <Form.Item
        name="identifier"
        label="Identifier"
        tooltip="Email address, service account ID, or agent identifier"
      >
        <Input placeholder="e.g. team@acme.com or agent:name-v1" />
      </Form.Item>

      <Form.Item name="platform" label="Platform">
        <Select
          allowClear
          placeholder="Select platform"
          options={PLATFORM_OPTIONS}
          aria-label="Platform"
        />
      </Form.Item>

      <Form.Item
        name="purposes"
        label="Approved purposes"
        tooltip="Which purposes is this consumer authorized for?"
      >
        <Select
          mode="multiple"
          placeholder="Select purposes"
          options={MOCK_PURPOSE_OPTIONS}
          aria-label="Approved purposes"
        />
      </Form.Item>

      <Form.Item name="description" label="Description">
        <Input.TextArea placeholder="Enter a description" rows={3} />
      </Form.Item>

      <Flex justify="space-between" className="pt-4">
        <Button onClick={handleCancel}>Cancel</Button>
        <Button type="primary" htmlType="submit">
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default DataConsumerForm;
