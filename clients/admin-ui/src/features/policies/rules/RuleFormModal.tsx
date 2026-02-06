import {
  Form,
  Input,
  Modal,
  Select,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo } from "react";

import {
  useCreateOrUpdateRulesMutation,
  useCreateOrUpdateTargetsMutation,
} from "~/features/policy/policy.slice";
import {
  ActionType,
  RuleResponseWithTargets,
  RuleTarget,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface RuleFormValues {
  name: string;
  key: string;
  action_type: ActionType;
  targets: string[];
  masking_strategy?: string;
  storage_destination_key?: string;
}

interface RuleFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyKey: string;
  rule?: RuleResponseWithTargets;
}

const actionTypeOptions = [
  { value: ActionType.ACCESS, label: "Access" },
  { value: ActionType.ERASURE, label: "Erasure" },
  { value: ActionType.CONSENT, label: "Consent" },
  { value: ActionType.UPDATE, label: "Update" },
];

const maskingStrategyOptions = [
  { value: "null_rewrite", label: "Null Rewrite" },
  { value: "string_rewrite", label: "String Rewrite" },
  { value: "hash", label: "Hash" },
  { value: "random_string_rewrite", label: "Random String" },
  { value: "aes_encrypt", label: "AES Encrypt" },
  { value: "hmac", label: "HMAC" },
];

// Common data categories for quick selection
const commonDataCategories = [
  "user",
  "user.contact",
  "user.contact.email",
  "user.contact.phone_number",
  "user.contact.address",
  "user.name",
  "user.demographic",
  "user.biometric",
  "user.financial",
  "user.credentials",
  "user.device",
  "user.browsing_history",
  "user.location",
  "user.unique_id",
];

const RuleFormModal = ({
  isOpen,
  onClose,
  policyKey,
  rule,
}: RuleFormModalProps) => {
  const [form] = Form.useForm<RuleFormValues>();
  const message = useMessage();
  const isEditing = !!rule;

  const [createOrUpdateRules, { isLoading: isRuleLoading }] =
    useCreateOrUpdateRulesMutation();
  const [createOrUpdateTargets, { isLoading: isTargetsLoading }] =
    useCreateOrUpdateTargetsMutation();

  const isLoading = isRuleLoading || isTargetsLoading;

  const actionType = Form.useWatch("action_type", form);
  const isAccessRule = actionType === ActionType.ACCESS;
  const isErasureRule = actionType === ActionType.ERASURE;

  // Extract existing target data categories
  const existingTargets = useMemo(() => {
    if (!rule?.targets) {
      return [];
    }
    return rule.targets.map((t: RuleTarget) => t.data_category);
  }, [rule?.targets]);

  // Populate form when editing
  useEffect(() => {
    if (rule && isEditing) {
      form.setFieldsValue({
        name: rule.name,
        key: rule.key ?? "",
        action_type: rule.action_type,
        targets: existingTargets,
        masking_strategy: rule.masking_strategy?.strategy,
      });
    }
  }, [rule, isEditing, form, existingTargets]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      form.resetFields();
    }
  }, [isOpen, form]);

  const handleSubmit = useCallback(
    async (values: RuleFormValues) => {
      // Build rule data
      const ruleData = {
        name: values.name,
        key: values.key,
        action_type: values.action_type,
        masking_strategy:
          values.action_type === ActionType.ERASURE && values.masking_strategy
            ? { strategy: values.masking_strategy, configuration: {} }
            : null,
        storage_destination_key:
          values.action_type === ActionType.ACCESS
            ? values.storage_destination_key || null
            : null,
      };

      // Create/update the rule
      const ruleResult = await createOrUpdateRules({
        policyKey,
        rules: [ruleData],
      });

      if (isErrorResult(ruleResult)) {
        message.error("Failed to save rule. Please try again.");
        return;
      }

      if (ruleResult.data.failed.length > 0) {
        message.error(`Failed to save rule: ${ruleResult.data.failed[0].message}`);
        return;
      }

      // If we have targets, update them
      if (values.targets && values.targets.length > 0) {
        const targetData = values.targets.map((dataCategory, index) => ({
          name: `${values.key}_target_${index}`,
          key: `${values.key}_target_${dataCategory.replace(/\./g, "_")}`,
          data_category: dataCategory,
        }));

        const targetsResult = await createOrUpdateTargets({
          policyKey,
          ruleKey: values.key,
          targets: targetData,
        });

        if (isErrorResult(targetsResult)) {
          message.warning("Rule saved but failed to update targets.");
        }
      }

      message.success(
        isEditing ? "Rule updated successfully" : "Rule created successfully"
      );
      onClose();
    },
    [
      createOrUpdateRules,
      createOrUpdateTargets,
      policyKey,
      isEditing,
      message,
      onClose,
    ]
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
      title={isEditing ? "Edit rule" : "Add rule"}
      open={isOpen}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText={isEditing ? "Save" : "Add"}
      confirmLoading={isLoading}
      destroyOnClose
      width={600}
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
            placeholder="Enter rule name"
            onChange={handleNameChange}
            data-testid="rule-name-input"
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
        >
          <Input
            placeholder="rule_key"
            disabled={isEditing}
            data-testid="rule-key-input"
          />
        </Form.Item>

        <Form.Item
          name="action_type"
          label="Action type"
          rules={[{ required: true, message: "Action type is required" }]}
        >
          <Select
            placeholder="Select action type"
            options={actionTypeOptions}
            data-testid="rule-action-type-select"
          />
        </Form.Item>

        <Form.Item
          name="targets"
          label="Data category targets"
          tooltip="Select the data categories this rule should apply to"
        >
          <Select
            mode="tags"
            placeholder="Select or type data categories"
            options={commonDataCategories.map((cat) => ({
              value: cat,
              label: cat,
            }))}
            data-testid="rule-targets-select"
          />
        </Form.Item>

        {isErasureRule && (
          <Form.Item
            name="masking_strategy"
            label="Masking strategy"
            tooltip="How matched data will be masked for erasure requests"
          >
            <Select
              placeholder="Select masking strategy"
              options={maskingStrategyOptions}
              allowClear
              data-testid="rule-masking-strategy-select"
            />
          </Form.Item>
        )}

        {isAccessRule && (
          <Form.Item
            name="storage_destination_key"
            label="Storage destination key"
            tooltip="The key of the storage destination for access request results"
          >
            <Input
              placeholder="Enter storage destination key"
              data-testid="rule-storage-destination-input"
            />
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
};

export default RuleFormModal;
