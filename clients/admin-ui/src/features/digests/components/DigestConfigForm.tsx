import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntSelect as Select,
  AntSpace as Space,
  AntSwitch as Switch,
  AntTypography as Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { NOTIFICATIONS_DIGESTS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { DigestType, MessagingMethod, ScopeRegistryEnum } from "~/types/api";

import {
  DEFAULT_CRON_EXPRESSION,
  DEFAULT_TIMEZONE,
  MESSAGING_METHOD_LABELS,
} from "../constants";
import {
  useCreateDigestConfigMutation,
  useDeleteDigestConfigMutation,
  useUpdateDigestConfigMutation,
} from "../digest-config.slice";
import type { DigestConfigFormValues } from "../types";
import TestEmailModal from "./TestEmailModal";

const { Text } = Typography;
const { TextArea } = Input;

interface DigestConfigFormProps {
  initialValues?: DigestConfigFormValues;
  isLoading?: boolean;
}

const DigestConfigForm = ({
  initialValues,
  isLoading,
}: DigestConfigFormProps) => {
  const [form] = Form.useForm<DigestConfigFormValues>();
  const router = useRouter();
  const [messageApi, messageContext] = message.useMessage();
  const [testEmailModalOpen, setTestEmailModalOpen] = useState(false);

  const [createDigestConfig, { isLoading: isCreating }] =
    useCreateDigestConfigMutation();
  const [updateDigestConfig, { isLoading: isUpdating }] =
    useUpdateDigestConfigMutation();
  const [deleteDigestConfig, { isLoading: isDeleting }] =
    useDeleteDigestConfigMutation();

  const showDeleteButton =
    useHasPermission([ScopeRegistryEnum.DIGEST_CONFIG_DELETE]) &&
    !!initialValues?.id;

  const isEditMode = !!initialValues?.id;

  const handleDelete = async () => {
    if (!initialValues?.id) {
      return;
    }

    const result = await deleteDigestConfig({
      config_id: initialValues.id,
      digest_config_type: DigestType.MANUAL_TASKS,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }

    messageApi.success(
      "Digest configuration deleted successfully",
      undefined,
      () => {
        router.push(NOTIFICATIONS_DIGESTS_ROUTE);
      },
    );
  };

  const onSubmit = async (values: DigestConfigFormValues) => {
    const { id, ...requestData } = values;

    if (isEditMode && id) {
      // Update existing
      const result = await updateDigestConfig({
        config_id: id,
        digest_config_type: DigestType.MANUAL_TASKS,
        data: requestData,
      });

      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        return;
      }

      messageApi.success("Digest configuration updated successfully");
    } else {
      // Create new
      const result = await createDigestConfig({
        digest_config_type: DigestType.MANUAL_TASKS,
        data: requestData,
      });

      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        return;
      }

      messageApi.success("Digest configuration created successfully");
    }

    router.push(NOTIFICATIONS_DIGESTS_ROUTE);
  };

  const defaultValues = initialValues || {
    name: "",
    description: "",
    digest_type: DigestType.MANUAL_TASKS,
    enabled: true,
    messaging_service_type: MessagingMethod.EMAIL,
    cron_expression: DEFAULT_CRON_EXPRESSION,
    timezone: DEFAULT_TIMEZONE,
    config_metadata: null,
  };

  if (isLoading) {
    return <div>Loading...</div>; // TODO: Add skeleton loader
  }

  return (
    <>
      {messageContext}
      <Form
        form={form}
        layout="vertical"
        initialValues={defaultValues}
        onFinish={onSubmit}
        className="max-w-2xl"
      >
        <div className="flex gap-4">
          <Form.Item
            label="Digest Type"
            name="digest_type"
            tooltip="Type of content this digest will contain"
            className="flex-1"
          >
            <Select
              disabled
              options={[
                {
                  label: "Manual Tasks",
                  value: DigestType.MANUAL_TASKS,
                },
              ]}
              data-testid="select-digest-type"
            />
          </Form.Item>

          <Form.Item
            label="Messaging Method"
            name="messaging_service_type"
            tooltip="How the digest will be delivered"
            className="flex-1"
          >
            <Select
              disabled
              options={[
                {
                  label: MESSAGING_METHOD_LABELS[MessagingMethod.EMAIL],
                  value: MessagingMethod.EMAIL,
                },
              ]}
              data-testid="select-messaging-method"
            />
          </Form.Item>
        </div>

        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Please enter a name" }]}
          tooltip="A descriptive name for this digest configuration"
        >
          <Input
            data-testid="input-name"
            placeholder="e.g., Weekly Manual Tasks Summary"
          />
        </Form.Item>

        <Form.Item
          label="Description"
          name="description"
          tooltip="Optional description to help identify this digest"
        >
          <TextArea
            rows={3}
            data-testid="input-description"
            placeholder="Brief description of what this digest is for"
          />
        </Form.Item>

        <Form.Item
          label="Cron Expression"
          name="cron_expression"
          rules={[
            { required: true, message: "Please enter a cron expression" },
          ]}
          tooltip="Cron expression for scheduling (e.g., '0 9 * * 1' for Monday at 9 AM)"
          extra={
            <Text type="secondary" className="text-xs">
              Note: A cron builder UI will be added in a future update
            </Text>
          }
        >
          <Input
            data-testid="input-cron"
            placeholder="0 9 * * 1"
            className="font-mono"
          />
        </Form.Item>

        <Form.Item
          label="Timezone"
          name="timezone"
          rules={[{ required: true, message: "Please enter a timezone" }]}
          tooltip="Timezone for the cron schedule (e.g., 'UTC', 'America/New_York')"
          extra={
            <Text type="secondary" className="text-xs">
              Note: A timezone picker will be added in a future update
            </Text>
          }
        >
          <Input data-testid="input-timezone" placeholder="UTC" />
        </Form.Item>

        <Form.Item
          label="Enabled"
          name="enabled"
          valuePropName="checked"
          tooltip="Enable or disable this digest"
        >
          <Switch data-testid="switch-enabled" />
        </Form.Item>

        {/* Form Actions */}
        <Form.Item>
          <Space className="w-full justify-between">
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={isCreating || isUpdating}
                data-testid="submit-btn"
              >
                {isEditMode ? "Update" : "Create"}
              </Button>
              <Button
                onClick={() => router.push(NOTIFICATIONS_DIGESTS_ROUTE)}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
            </Space>

            <Space>
              {isEditMode && (
                <Button
                  onClick={() => setTestEmailModalOpen(true)}
                  data-testid="test-email-btn"
                >
                  Send Test Email
                </Button>
              )}
              {showDeleteButton && (
                <Button
                  danger
                  onClick={handleDelete}
                  loading={isDeleting}
                  data-testid="delete-btn"
                >
                  Delete
                </Button>
              )}
            </Space>
          </Space>
        </Form.Item>
      </Form>

      {/* Test Email Modal */}
      {isEditMode && (
        <TestEmailModal
          isOpen={testEmailModalOpen}
          onClose={() => setTestEmailModalOpen(false)}
          digestType={DigestType.MANUAL_TASKS}
        />
      )}
    </>
  );
};

export default DigestConfigForm;
