import { Card, Empty, Form, Input, Space } from "fidesui";
import { useState } from "react";

import { ActionEditModal, ActionFormValues } from "./ActionEditModal";
import { ActionsTable } from "./ActionsTable";

export interface PrivacyCenterConfigValue {
  title?: string;
  description?: string;
  logo_path?: string;
  actions?: Array<
    ActionFormValues & {
      custom_privacy_request_fields?: Record<string, unknown>;
      _form_builder_spec?: { spec: unknown; version: number };
    }
  >;
}

interface PrivacyCenterConfigSectionProps {
  propertyId: string;
  value?: PrivacyCenterConfigValue | null;
  onChange?: (next: PrivacyCenterConfigValue) => void;
}

export const PrivacyCenterConfigSection = ({
  propertyId,
  value,
  onChange,
}: PrivacyCenterConfigSectionProps) => {
  const [editing, setEditing] = useState<ActionFormValues | null>(null);
  const [open, setOpen] = useState(false);

  const isInitialized = !!value;

  const handleAdd = () => {
    setEditing(null);
    setOpen(true);
  };

  const handleEdit = (action: ActionFormValues) => {
    setEditing(action);
    setOpen(true);
  };

  const handleOk = (action: ActionFormValues) => {
    const current = value ?? { actions: [] };
    const existingActions = current.actions ?? [];
    const isUpdate = existingActions.some(
      (a) => a.policy_key === action.policy_key,
    );
    const nextActions = isUpdate
      ? existingActions.map((a) =>
          a.policy_key === action.policy_key ? { ...a, ...action } : a,
        )
      : [...existingActions, action];

    onChange?.({ ...current, actions: nextActions });
    setOpen(false);
  };

  if (!isInitialized) {
    return (
      <Card title="Privacy center config">
        <Empty description="No privacy center config yet.">
          <button
            type="button"
            onClick={() =>
              onChange?.({
                title: "",
                description: "",
                logo_path: "",
                actions: [],
                // The backend's PrivacyCenterConfig schema requires a
                // non-empty `consent` block. v1 doesn't surface consent
                // editing in this UI, so we seed minimal placeholder
                // content. Users can edit it later via JSON or once a
                // consent UI is added.
                consent: {
                  button: {
                    description: "Manage your consent preferences.",
                    icon_path: "/consent.svg",
                    identity_inputs: { email: "required" },
                    title: "Manage your consent",
                  },
                  page: {
                    description: "Manage your consent preferences.",
                    title: "Consent",
                    consentOptions: [],
                  },
                },
              } as unknown as PrivacyCenterConfigValue)
            }
          >
            Set up privacy center config
          </button>
        </Empty>
      </Card>
    );
  }

  return (
    <Card title="Privacy center config">
      <Space direction="vertical" style={{ width: "100%" }}>
        <Form.Item label="Title">
          <Input
            value={value?.title ?? ""}
            onChange={(e) =>
              onChange?.({ ...(value ?? {}), title: e.target.value })
            }
          />
        </Form.Item>
        <Form.Item label="Description">
          <Input.TextArea
            value={value?.description ?? ""}
            onChange={(e) =>
              onChange?.({ ...(value ?? {}), description: e.target.value })
            }
          />
        </Form.Item>
        <Form.Item label="Logo path">
          <Input
            value={value?.logo_path ?? ""}
            onChange={(e) =>
              onChange?.({ ...(value ?? {}), logo_path: e.target.value })
            }
          />
        </Form.Item>
        <ActionsTable
          propertyId={propertyId}
          actions={value?.actions ?? []}
          onEditAction={handleEdit}
          onAddAction={handleAdd}
        />
      </Space>
      <ActionEditModal
        open={open}
        initial={editing}
        onCancel={() => setOpen(false)}
        onOk={handleOk}
      />
    </Card>
  );
};
