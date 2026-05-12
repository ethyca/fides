import { Form, Input, InputNumber, Select, useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { capitalize } from "~/features/common/utils";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  useCreateOrUpdatePoliciesMutation,
  useGetPolicyQuery,
} from "~/features/policies/policy.slice";
import { ActionType } from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface PolicyFormValues {
  name: string;
  key: string;
  execution_timeframe?: number | null;
  action_type?: ActionType;
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

  const initialValues = useMemo<PolicyFormValues | undefined>(
    () =>
      isEditing && existingPolicy
        ? {
            name: existingPolicy.name,
            key: existingPolicy.key ?? "",
            execution_timeframe: existingPolicy.execution_timeframe,
            action_type: existingPolicy.rules?.[0]?.action_type,
          }
        : undefined,
    [isEditing, existingPolicy],
  );

  const handleClose = useCallback(() => {
    form.resetFields();
    onClose();
  }, [form, onClose]);

  const handleSubmit = useCallback(
    async (values: PolicyFormValues) => {
      const result = await createOrUpdatePolicy([
        {
          name: values.name,
          key: values.key,
          execution_timeframe: values.execution_timeframe ?? null,
          ...(isEditing ? {} : { action_type: values.action_type }),
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
      handleClose();

      if (!isEditing && result.data.succeeded.length > 0) {
        const newPolicy = result.data.succeeded[0];
        router.push({
          pathname: POLICY_DETAIL_ROUTE,
          query: { key: newPolicy.key },
        });
      }
    },
    [createOrUpdatePolicy, isEditing, message, handleClose, router],
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
    <ConfirmCloseModal
      title={isEditing ? "Edit policy" : "Create policy"}
      open={isOpen}
      onClose={handleClose}
      getIsDirty={() => form.isFieldsTouched()}
      onOk={() => form.submit()}
      okText={isEditing ? "Save" : "Create"}
      confirmLoading={isLoading}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={initialValues}
        key={existingPolicy?.key ?? "create"}
      >
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
            { required: !isEditing, message: "Key is required" },
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
          name="action_type"
          label="Request type"
          rules={[
            { required: !isEditing, message: "Request type is required" },
          ]}
          tooltip="Determines the request type and auto-generates a default rule."
        >
          <Select
            placeholder="Select a request type"
            data-testid="policy-type-select"
            disabled={isEditing}
            aria-label="Request type"
            options={[
              ActionType.ACCESS,
              ActionType.ERASURE,
              ActionType.CONSENT,
            ].map((type) => ({ value: type, label: capitalize(type) }))}
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
    </ConfirmCloseModal>
  );
};
