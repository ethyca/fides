import { Form, Input, Modal, Select } from "fidesui";
import { useMemo } from "react";

import { useGetPoliciesQuery } from "~/features/policies/policy.slice";

export interface ActionFormValues {
  policy_key: string;
  title: string;
  description: string;
  icon_path: string;
  identity_inputs?: Record<string, "required" | "optional">;
}

interface ActionEditModalProps {
  open: boolean;
  initial: ActionFormValues | null;
  onOk: (values: ActionFormValues) => void;
  onCancel: () => void;
}

export const ActionEditModal = ({
  open,
  initial,
  onOk,
  onCancel,
}: ActionEditModalProps) => {
  const [form] = Form.useForm<ActionFormValues>();

  const { data: policiesData, isLoading: isLoadingPolicies } =
    useGetPoliciesQuery();

  const initialPolicyKey = initial?.policy_key;
  const policyOptions = useMemo(() => {
    const options =
      policiesData?.items.map((p) => ({
        label: p.name,
        value: p.key ?? "",
      })) ?? [];

    const hasInitial = options.some((o) => o.value === initialPolicyKey);
    if (initialPolicyKey && !hasInitial && !isLoadingPolicies) {
      options.push({
        label: `${initialPolicyKey} (not found)`,
        value: initialPolicyKey,
      });
    }
    return options;
  }, [policiesData, initialPolicyKey, isLoadingPolicies]);

  const isStalePolicy =
    !!initialPolicyKey &&
    !isLoadingPolicies &&
    !policiesData?.items.some((p) => p.key === initialPolicyKey);

  return (
    <Modal
      open={open}
      title={initial ? "Edit action" : "Add action"}
      okText="Save"
      onOk={async () => {
        const values = await form.validateFields();
        onOk(values);
      }}
      onCancel={onCancel}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={initial ?? { identity_inputs: { email: "required" } }}
      >
        <Form.Item
          label="Policy"
          name="policy_key"
          rules={[{ required: true }]}
          validateStatus={isStalePolicy ? "warning" : undefined}
          help={
            isStalePolicy
              ? "This policy no longer exists. Pick a different one to save."
              : undefined
          }
        >
          <Select
            options={policyOptions}
            loading={isLoadingPolicies}
            showSearch
            optionFilterProp="label"
            placeholder="Select a policy"
            aria-label="Policy"
          />
        </Form.Item>
        <Form.Item label="Title" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item
          label="Description"
          name="description"
          rules={[{ required: true }]}
        >
          <Input.TextArea autoSize />
        </Form.Item>
        <Form.Item
          label="Icon path"
          name="icon_path"
          rules={[{ required: true }]}
        >
          <Input placeholder="/icon.svg" />
        </Form.Item>
        <Form.Item
          label="Identity inputs"
          name={["identity_inputs", "email"]}
          tooltip="Whether the privacy center asks for email before this action."
        >
          <Select
            aria-label="Identity inputs"
            options={[
              { label: "Email required", value: "required" },
              { label: "Email optional", value: "optional" },
            ]}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
