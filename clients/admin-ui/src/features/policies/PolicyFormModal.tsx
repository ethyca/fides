import { Form, Input, InputNumber, Modal, useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect } from "react";

import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  useCreateOrUpdatePoliciesMutation,
  useGetPolicyQuery,
} from "~/features/policies/policy.slice";
import { isErrorResult } from "~/types/errors";

interface PolicyFormValues {
  name: string;
  key: string;
  execution_timeframe?: number | null;
}

interface PolicyFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyKey?: string;
}

export const PolicyFormModal = ({
  isOpen,
  onClose,
  policyKey,
}: PolicyFormModalProps) => {
  const [form] = Form.useForm<PolicyFormValues>();
  const router = useRouter();
  const message = useMessage();
  const isEditing = !!policyKey;

  const { data: existingPolicy } = useGetPolicyQuery(policyKey!, {
    skip: !policyKey,
  });

  const [createOrUpdatePolicy, { isLoading }] =
    useCreateOrUpdatePoliciesMutation();

  useEffect(() => {
    if (existingPolicy && isEditing) {
      form.setFieldsValue({
        name: existingPolicy.name,
        key: existingPolicy.key ?? "",
        execution_timeframe: existingPolicy.execution_timeframe,
      });
    }
  }, [existingPolicy, isEditing, form]);

  useEffect(() => {
    if (!isOpen) {
      form.resetFields();
    }
  }, [isOpen, form]);

  const handleSubmit = useCallback(
    async (values: PolicyFormValues) => {
      const result = await createOrUpdatePolicy([
        {
          name: values.name,
          key: values.key,
          execution_timeframe: values.execution_timeframe ?? null,
        },
      ]);

      if (isErrorResult(result)) {
        message.error("Failed to save policy. Please try again.");
        return;
      }

      if (result.data.failed.length > 0) {
        message.error(
          `Failed to save policy: ${result.data.failed[0].message}`,
        );
        return;
      }

      message.success(
        isEditing
          ? "Policy updated successfully"
          : "Policy created successfully",
      );
      onClose();

      if (!isEditing && result.data.succeeded.length > 0) {
        const newPolicy = result.data.succeeded[0];
        router.push({
          pathname: POLICY_DETAIL_ROUTE,
          query: { key: newPolicy.key },
        });
      }
    },
    [createOrUpdatePolicy, isEditing, message, onClose, router],
  );

  const handleNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!isEditing) {
        form.setFieldValue("key", formatKey(e.target.value));
      }
    },
    [form, isEditing],
  );

  return (
    <Modal
      title={isEditing ? "Edit policy" : "Create policy"}
      open={isOpen}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText={isEditing ? "Save" : "Create"}
      confirmLoading={isLoading}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          name="name"
          label="Name"
          rules={[{ required: true, message: "Name is required" }]}
        >
          <Input
            placeholder="Enter policy name"
            onChange={handleNameChange}
            data-testid="policy-name-input"
          />
        </Form.Item>

        <Form.Item
          name="key"
          label="Key"
          rules={[
            { required: true, message: "Key is required" },
            {
              pattern: /^[a-z0-9_]+$/,
              message:
                "Key must contain only lowercase letters, numbers, and underscores",
            },
          ]}
          tooltip="Unique identifier for the policy. Auto-generated from name."
        >
          <Input
            placeholder="policy_key"
            disabled={isEditing}
            data-testid="policy-key-input"
          />
        </Form.Item>

        <Form.Item
          name="execution_timeframe"
          label="Execution timeframe (days)"
          tooltip="Time in days to fulfill privacy requests using this policy"
        >
          <InputNumber
            min={1}
            placeholder="Enter days"
            className="w-full"
            data-testid="policy-timeframe-input"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
