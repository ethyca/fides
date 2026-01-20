import { Button, Flex, Form, Input, Modal, Typography } from "fidesui";
import { useState } from "react";

import { EvaluateSubjectContext } from "./types";

const { Text } = Typography;

interface EvaluateOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEvaluate: (subjectContext?: EvaluateSubjectContext) => void;
  policyName?: string;
  isLoading?: boolean;
}

export const EvaluateOptionsModal = ({
  isOpen,
  onClose,
  onEvaluate,
  policyName,
  isLoading = false,
}: EvaluateOptionsModalProps) => {
  const [form] = Form.useForm();
  const [hasSubjectContext, setHasSubjectContext] = useState(false);

  const handleSubmit = (values: EvaluateSubjectContext) => {
    // Filter out empty values
    const subjectContext: EvaluateSubjectContext = {};
    if (values.email?.trim()) {
      subjectContext.email = values.email.trim();
    }
    if (values.phone_number?.trim()) {
      subjectContext.phone_number = values.phone_number.trim();
    }
    if (values.fides_user_device_id?.trim()) {
      subjectContext.fides_user_device_id = values.fides_user_device_id.trim();
    }
    if (values.external_id?.trim()) {
      subjectContext.external_id = values.external_id.trim();
    }

    // If no subject context provided, pass undefined
    const hasAnyValue = Object.keys(subjectContext).length > 0;
    onEvaluate(hasAnyValue ? subjectContext : undefined);
  };

  const handleValuesChange = (_: unknown, allValues: EvaluateSubjectContext) => {
    const hasAny = !!(
      allValues.email?.trim() ||
      allValues.phone_number?.trim() ||
      allValues.fides_user_device_id?.trim() ||
      allValues.external_id?.trim()
    );
    setHasSubjectContext(hasAny);
  };

  const handleClose = () => {
    form.resetFields();
    setHasSubjectContext(false);
    onClose();
  };

  const title = policyName
    ? `Evaluate Policy: ${policyName}`
    : "Evaluate All Policies";

  return (
    <Modal
      title={title}
      open={isOpen}
      onCancel={handleClose}
      footer={null}
      width={500}
      destroyOnClose
    >
      <Flex vertical gap="middle">
        <Text type="secondary">
          Optionally provide a data subject identity to test consent-based
          constraints. Leave all fields empty to evaluate without subject
          context.
        </Text>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          onValuesChange={handleValuesChange}
        >
          <Form.Item
            label="Email"
            name="email"
            tooltip="Email address of the data subject"
          >
            <Input
              placeholder="user@example.com"
              data-testid="subject-email"
            />
          </Form.Item>

          <Form.Item
            label="Phone Number"
            name="phone_number"
            tooltip="Phone number of the data subject"
          >
            <Input
              placeholder="+1234567890"
              data-testid="subject-phone"
            />
          </Form.Item>

          <Form.Item
            label="Fides User Device ID"
            name="fides_user_device_id"
            tooltip="Device identifier for the data subject"
          >
            <Input
              placeholder="device-uuid-1234"
              data-testid="subject-device-id"
            />
          </Form.Item>

          <Form.Item
            label="External ID"
            name="external_id"
            tooltip="External identifier for the data subject"
          >
            <Input
              placeholder="ext-user-123"
              data-testid="subject-external-id"
            />
          </Form.Item>

          <Flex justify="flex-end" gap="small" style={{ marginTop: 16 }}>
            <Button onClick={handleClose}>Cancel</Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              data-testid="run-evaluate-btn"
            >
              {hasSubjectContext
                ? "Evaluate with Subject"
                : "Evaluate without Subject"}
            </Button>
          </Flex>
        </Form>
      </Flex>
    </Modal>
  );
};
