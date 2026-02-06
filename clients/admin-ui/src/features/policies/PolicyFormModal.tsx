import {
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect } from "react";

import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import {
  useCreateOrUpdatePoliciesMutation,
  useGetPolicyQuery,
} from "~/features/policy/policy.slice";
import { DrpAction, PolicyResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface PolicyFormValues {
  name: string;
  key: string;
  drp_action?: DrpAction | null;
  execution_timeframe?: number | null;
}

interface PolicyFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyKey?: string; // If provided, editing existing policy
}

const drpActionOptions = [
  { value: DrpAction.ACCESS, label: "Access" },
  { value: DrpAction.DELETION, label: "Deletion" },
  { value: DrpAction.SALE_OPT_OUT, label: "Sale Opt-Out" },
  { value: DrpAction.SALE_OPT_IN, label: "Sale Opt-In" },
  { value: DrpAction.ACCESS_CATEGORIES, label: "Access Categories" },
  { value: DrpAction.ACCESS_SPECIFIC, label: "Access Specific" },
];

const PolicyFormModal = ({
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

  // Populate form when editing
  useEffect(() => {
    if (existingPolicy && isEditing) {
      form.setFieldsValue({
        name: existingPolicy.name,
        key: existingPolicy.key ?? "",
        drp_action: existingPolicy.drp_action,
        execution_timeframe: existingPolicy.execution_timeframe,
      });
    }
  }, [existingPolicy, isEditing, form]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      form.resetFields();
    }
  }, [isOpen, form]);

  const handleSubmit = useCallback(
    async (values: PolicyFormValues) => {
      const policyData = {
        name: values.name,
        key: values.key,
        drp_action: values.drp_action || null,
        execution_timeframe: values.execution_timeframe || null,
      };

      const result = await createOrUpdatePolicy([policyData]);

      if (isErrorResult(result)) {
        message.error("Failed to save policy. Please try again.");
        return;
      }

      if (result.data.failed.length > 0) {
        message.error(
          `Failed to save policy: ${result.data.failed[0].message}`
        );
        return;
      }

      message.success(
        isEditing ? "Policy updated successfully" : "Policy created successfully"
      );
      onClose();

      // Navigate to the new policy if creating
      if (!isEditing && result.data.succeeded.length > 0) {
        const newPolicy = result.data.succeeded[0];
        router.push({
          pathname: POLICY_DETAIL_ROUTE,
          query: { key: newPolicy.key },
        });
      }
    },
    [createOrUpdatePolicy, isEditing, message, onClose, router]
  );

  // Auto-generate key from name
  const handleNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!isEditing) {
        const generatedKey = e.target.value
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_|_$/g, "");
        form.setFieldValue("key", generatedKey);
      }
    },
    [form, isEditing]
  );

  return (
    <Modal
      title={isEditing ? "Edit policy" : "Create policy"}
      open={isOpen}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText={isEditing ? "Save" : "Create"}
      confirmLoading={isLoading}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        className="mt-4"
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
            { required: true, message: "Key is required" },
            {
              pattern: /^[a-z0-9_]+$/,
              message: "Key must contain only lowercase letters, numbers, and underscores",
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
          name="drp_action"
          label="Action"
          tooltip="Data Rights Protocol action to associate with this policy"
        >
          <Select
            placeholder="Select action (optional)"
            options={drpActionOptions}
            allowClear
            data-testid="policy-drp-action-select"
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

export default PolicyFormModal;
