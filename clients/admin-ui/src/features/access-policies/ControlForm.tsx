import { Button, Flex, Form, Input } from "fidesui";
import { useMemo } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { CONTROLS_ROUTE } from "~/features/common/nav/routes";

import type { Control } from "./access-policies.slice";

export interface ControlFormValues {
  label: string;
  description: string;
}

interface ControlFormProps {
  control?: Control;
  isSubmitting?: boolean;
  handleSubmit: (values: ControlFormValues) => Promise<void>;
}

const ControlForm = ({
  control,
  isSubmitting,
  handleSubmit,
}: ControlFormProps) => {
  const [form] = Form.useForm<ControlFormValues>();
  const isEditing = !!control;

  const initialValues = useMemo<ControlFormValues>(
    () => ({
      label: control?.label ?? "",
      description: control?.description ?? "",
    }),
    [control],
  );

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
        <Input placeholder="e.g. EEA & UK GDPR" />
      </Form.Item>

      <Form.Item name="description" label="Description">
        <Input.TextArea
          rows={3}
          placeholder="Describe the purpose of this control"
        />
      </Form.Item>

      <Flex gap="small">
        <Button type="primary" htmlType="submit" loading={isSubmitting}>
          {isEditing ? "Save" : "Create control"}
        </Button>
        <RouterLink href={CONTROLS_ROUTE}>
          <Button>Cancel</Button>
        </RouterLink>
      </Flex>
    </Form>
  );
};

export default ControlForm;
