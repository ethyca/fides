import { Button, Empty, Form, Input, Space, Switch } from "fidesui";
import { useEffect } from "react";

import type { ComponentType } from "./catalog";
import type { JsonRenderSpec } from "./mapper";

interface FieldPropertiesPanelProps {
  spec: JsonRenderSpec | null;
  selectedElementId: string | null;
  onUpdateField: (elementId: string, props: Record<string, unknown>) => void;
  onRemoveField: (elementId: string) => void;
}

type EditableType = Exclude<ComponentType, "Form">;

const panelStyle: React.CSSProperties = {
  height: "100%",
  display: "flex",
  flexDirection: "column",
  padding: 16,
  overflowY: "auto",
};

type FormValues = Record<string, unknown>;

const stripUndefined = (
  values: Record<string, unknown>,
): Record<string, unknown> => {
  const result: Record<string, unknown> = {};
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined && v !== "") {
      result[k] = v;
    }
  });
  return result;
};

// Editor for a list of string options. Used by Select / MultiSelect.
const OptionsEditor = ({
  value = [],
  onChange,
}: {
  value?: string[];
  onChange?: (next: string[]) => void;
}) => {
  const setItem = (idx: number, next: string) => {
    const copy = [...value];
    copy[idx] = next;
    onChange?.(copy);
  };
  const remove = (idx: number) => {
    onChange?.(value.filter((_, i) => i !== idx));
  };
  const append = () => {
    onChange?.([...value, `Option ${value.length + 1}`]);
  };
  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      {value.map((opt, idx) => (
        <Space.Compact
          // eslint-disable-next-line react/no-array-index-key
          key={idx}
          style={{ width: "100%" }}
        >
          <Input
            value={opt}
            onChange={(e) => setItem(idx, e.target.value)}
            data-testid={`option-input-${idx}`}
          />
          <Button
            onClick={() => remove(idx)}
            disabled={value.length <= 1}
            data-testid={`option-remove-${idx}`}
          >
            Remove
          </Button>
        </Space.Compact>
      ))}
      <Button onClick={append} block data-testid="option-add">
        + Add option
      </Button>
    </Space>
  );
};

const EmptyState = () => (
  <div style={panelStyle}>
    <Empty
      description="Select a field to edit its properties."
      style={{ marginTop: 64 }}
    />
  </div>
);

export const FieldPropertiesPanel = ({
  spec,
  selectedElementId,
  onUpdateField,
  onRemoveField,
}: FieldPropertiesPanelProps) => {
  const [form] = Form.useForm<FormValues>();

  const element = selectedElementId
    ? spec?.elements?.[selectedElementId]
    : null;

  // Reset form whenever the selection changes so inputs reflect the
  // current field's props.
  useEffect(() => {
    if (element) {
      form.resetFields();
      form.setFieldsValue(
        element.props as Parameters<typeof form.setFieldsValue>[0],
      );
    }
  }, [selectedElementId, element, form]);

  if (!element || !selectedElementId) {
    return <EmptyState />;
  }

  const componentType = element.type as EditableType;

  const handleValuesChange = (
    _changed: Partial<FormValues>,
    all: FormValues,
  ) => {
    onUpdateField(selectedElementId, stripUndefined(all));
  };

  return (
    <div style={panelStyle} data-testid="field-properties-panel">
      <h3 style={{ marginTop: 0, marginBottom: 4 }}>{componentType} field</h3>
      <p
        style={{
          marginBottom: 16,
          color: "var(--fidesui-color-text-secondary)",
        }}
      >
        Editing <code>{(element.props as { name?: string }).name}</code>
      </p>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={element.props}
      >
        <Form.Item
          label="Name"
          name="name"
          tooltip="Field key sent to the backend. snake_case, ≤ 64 chars."
          rules={[
            {
              required: true,
              pattern: /^[a-z][a-z0-9_]{0,63}$/,
              message: "snake_case, must start with a letter, ≤ 64 chars",
            },
          ]}
        >
          <Input data-testid="prop-name" />
        </Form.Item>
        <Form.Item label="Label" name="label" rules={[{ required: true }]}>
          <Input data-testid="prop-label" />
        </Form.Item>
        <Form.Item
          label="Required"
          name="required"
          valuePropName="checked"
          tooltip="Whether the user must fill this field before submitting."
        >
          <Switch data-testid="prop-required" />
        </Form.Item>

        {componentType === "Text" && (
          <>
            <Form.Item label="Default value" name="default_value">
              <Input data-testid="prop-default-value" />
            </Form.Item>
            <Form.Item
              label="Hidden"
              name="hidden"
              valuePropName="checked"
              tooltip="Hide this field on the privacy center form. Useful for query-param-driven values."
            >
              <Switch data-testid="prop-hidden" />
            </Form.Item>
            <Form.Item
              label="Query param key"
              name="query_param_key"
              tooltip="If set, this field's default value is read from the matching URL query parameter."
            >
              <Input data-testid="prop-query-param-key" />
            </Form.Item>
          </>
        )}

        {(componentType === "Select" || componentType === "MultiSelect") && (
          <>
            <Form.Item
              label="Options"
              name="options"
              rules={[{ required: true, message: "At least one option" }]}
            >
              <OptionsEditor />
            </Form.Item>
            <Form.Item label="Default value" name="default_value">
              <Input data-testid="prop-default-value" />
            </Form.Item>
          </>
        )}

        {componentType === "Location" && (
          <>
            <Form.Item
              label="Custom options"
              name="options"
              tooltip="Override the default country list. Leave empty for the built-in list."
            >
              <OptionsEditor />
            </Form.Item>
            <Form.Item
              label="IP geolocation hint"
              name="ip_geolocation_hint"
              valuePropName="checked"
              tooltip="Pre-fill the location based on the user's IP address (best-effort)."
            >
              <Switch data-testid="prop-ip-hint" />
            </Form.Item>
          </>
        )}
      </Form>
      <div style={{ flex: 1 }} />
      <Button
        danger
        block
        onClick={() => onRemoveField(selectedElementId)}
        data-testid="remove-field-button"
        style={{ marginTop: 16 }}
      >
        Remove field
      </Button>
    </div>
  );
};
