import { Button, Flex, Form, Input } from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { CONTROLS_ROUTE } from "~/features/common/nav/routes";

import type { Control } from "./access-policies.slice";

export interface ControlFormValues {
  key: string;
  label: string;
  description: string;
}

interface ControlFormProps {
  control?: Control;
  handleSubmit: (values: ControlFormValues) => Promise<void>;
}

/**
 * Slugify a label into a valid control key: lowercase, replace non-alphanumeric
 * runs with underscores, trim leading/trailing underscores.
 */
const slugify = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

const ControlForm = ({ control, handleSubmit }: ControlFormProps) => {
  const [form] = Form.useForm<ControlFormValues>();
  const router = useRouter();
  const isEditing = !!control;

  const initialValues = useMemo<ControlFormValues>(
    () => ({
      key: control?.key ?? "",
      label: control?.label ?? "",
      description: control?.description ?? "",
    }),
    [control],
  );

  const handleLabelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isEditing) {
      return;
    }
    const label = e.target.value;
    const currentKey = form.getFieldValue("key") as string;
    // Auto-slug only if the user hasn't manually edited the key
    if (!currentKey || currentKey === slugify(label.slice(0, -1) || "")) {
      form.setFieldValue("key", slugify(label));
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleSubmit}
    >
      <Form.Item
        name="label"
        label="Name"
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input placeholder="e.g. EEA & UK GDPR" onChange={handleLabelChange} />
      </Form.Item>

      <Form.Item
        name="key"
        label="Key"
        extra="Unique identifier. Lowercase letters, numbers, and underscores only."
        rules={[
          { required: true, message: "Key is required" },
          {
            pattern: /^[a-z0-9_]+$/,
            message: "Lowercase letters, numbers, and underscores only",
          },
        ]}
      >
        <Input placeholder="e.g. eea_uk_gdpr" disabled={isEditing} />
      </Form.Item>

      <Form.Item name="description" label="Description">
        <Input.TextArea
          rows={3}
          placeholder="Describe the purpose of this control"
        />
      </Form.Item>

      <Flex gap={8}>
        <Button type="primary" htmlType="submit">
          {isEditing ? "Save" : "Create control"}
        </Button>
        <Button onClick={() => router.push(CONTROLS_ROUTE)}>Cancel</Button>
      </Flex>
    </Form>
  );
};

export default ControlForm;
