import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntSelect as Select,
  AntSpace as Space,
  AntSwitch as Switch,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { NOTIFICATIONS_DIGESTS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { DigestType, MessagingMethod, ScopeRegistryEnum } from "~/types/api";

import { DEFAULT_CRON_EXPRESSION, DEFAULT_TIMEZONE } from "../constants";
import {
  useCreateDigestConfigMutation,
  useDeleteDigestConfigMutation,
  useUpdateDigestConfigMutation,
} from "../digest-config.slice";
import type { DigestConfigFormValues } from "../types";
import DigestSchedulePicker from "./DigestSchedulePicker";
import TestEmailModal from "./TestEmailModal";

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
  const [timezone, setTimezone] = useState<string>(
    initialValues?.timezone || DEFAULT_TIMEZONE,
  );

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

    // Ensure messaging_service_type is always set
    // For new digests, default to EMAIL. For edits, keep existing value
    const dataWithMessaging = {
      ...requestData,
      messaging_service_type:
        requestData.messaging_service_type || MessagingMethod.EMAIL,
      timezone, // Use browser timezone from state
    };

    if (isEditMode && id) {
      // Update existing
      const result = await updateDigestConfig({
        config_id: id,
        digest_config_type: DigestType.MANUAL_TASKS,
        data: dataWithMessaging,
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
        data: dataWithMessaging,
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
    digest_type: DigestType.MANUAL_TASKS,
    enabled: true,
    messaging_service_type: MessagingMethod.EMAIL, // Hardcoded to EMAIL
    cron_expression: DEFAULT_CRON_EXPRESSION,
    timezone: DEFAULT_TIMEZONE, // Always UTC
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
        <Form.Item
          label="Digest Type"
          name="digest_type"
          tooltip="Type of content this digest will contain"
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

        {/* Hidden field to preserve messaging_service_type */}
        <Form.Item name="messaging_service_type" hidden>
          <Input />
        </Form.Item>

        <Form.Item
          name="cron_expression"
          rules={[{ required: true, message: "Please configure a schedule" }]}
          tooltip="Configure when the digest should be sent"
        >
          <DigestSchedulePicker onTimezoneChange={setTimezone} />
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
