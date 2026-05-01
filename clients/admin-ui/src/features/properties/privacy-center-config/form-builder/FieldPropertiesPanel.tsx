import {
  Alert,
  Button,
  Form,
  Icons,
  Input,
  Space,
  Switch,
  useModal,
} from "fidesui";
import snakeCase from "lodash.snakecase";
import { useEffect, useRef } from "react";

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

// Editor for a list of string options. Used by Select / MultiSelect / Location.
const OptionsEditor = ({
  value = [],
  onChange,
  minItems = 1,
}: {
  value?: string[];
  onChange?: (next: string[]) => void;
  /** Minimum number of options to keep. Below this, remove is disabled. */
  minItems?: number;
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
    <Space orientation="vertical" style={{ width: "100%" }}>
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
            disabled={value.length <= minItems}
            data-testid={`option-remove-${idx}`}
            icon={<Icons.TrashCan />}
            aria-label={`Remove option ${idx + 1}`}
          />
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
    <Alert type="info" title="Select a field to edit its properties." />
  </div>
);

export const FieldPropertiesPanel = ({
  spec,
  selectedElementId,
  onUpdateField,
  onRemoveField,
}: FieldPropertiesPanelProps) => {
  const [form] = Form.useForm<FormValues>();
  const modal = useModal();
  // Auto-sync the field's name from its label until the user manually edits
  // the name. The flag is recomputed on every selection change based on
  // whether the existing name still matches snakeCase(label) — fields with
  // customized names start with auto-sync off.
  const autoSyncNameRef = useRef(true);

  const element = selectedElementId
    ? spec?.elements?.[selectedElementId]
    : null;

  const handleRemoveClick = () => {
    if (!selectedElementId || !element) {
      return;
    }
    const fieldName =
      (element.props as { name?: string }).name ?? selectedElementId;
    modal.confirm({
      title: "Remove field?",
      content: (
        <span>
          This will remove <code>{fieldName}</code> from the form. You can undo
          this by adding the field again before saving.
        </span>
      ),
      okText: "Remove",
      okButtonProps: { danger: true },
      centered: true,
      onOk: () => onRemoveField(selectedElementId),
    });
  };

  // Re-sync the form ONLY when the selection changes — not when the
  // element's props change. The antd Form is the source of truth while
  // the user is typing; re-applying setFieldsValue on every keystroke
  // would steal focus from inputs (especially the Options editor).
  // The exhaustive-deps disable here is intentional: depending on `element`
  // (which is recomputed every render) would trigger setFieldsValue on every
  // keystroke and steal focus.
  useEffect(() => {
    if (!element) {
      return;
    }
    form.resetFields();
    form.setFieldsValue(
      element.props as Parameters<typeof form.setFieldsValue>[0],
    );
    const props = element.props as { name?: string; label?: string };
    // Auto-sync name only when the existing name matches snakeCase(label).
    // If the user has customized either field, leave them alone.
    autoSyncNameRef.current =
      typeof props.name === "string" &&
      typeof props.label === "string" &&
      props.name === snakeCase(props.label);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedElementId]);

  if (!element || !selectedElementId) {
    return <EmptyState />;
  }

  const componentType = element.type as EditableType;

  const handleValuesChange = (
    changed: Partial<FormValues>,
    all: FormValues,
  ) => {
    // The user manually edited the name field — stop auto-syncing it.
    if ("name" in changed) {
      autoSyncNameRef.current = false;
    }
    // While auto-sync is on, derive the name from the label. Skip if we'd
    // collide with another field's name.
    let next = all;
    let pendingNameSync: string | null = null;
    if (
      "label" in changed &&
      typeof changed.label === "string" &&
      autoSyncNameRef.current
    ) {
      const derived = snakeCase(changed.label);
      const collision = Object.entries(spec?.elements ?? {}).some(
        ([id, el]) =>
          id !== selectedElementId &&
          (el.props as { name?: string }).name === derived,
      );
      if (derived && !collision) {
        next = { ...all, name: derived };
        pendingNameSync = derived;
      }
    }
    // Hidden + required is contradictory — if the user can't see the
    // field, they can't fill it in. When Hidden turns on, clear required.
    let pendingRequiredSync = false;
    if ("hidden" in changed && changed.hidden === true && next.required) {
      next = { ...next, required: false };
      pendingRequiredSync = true;
    }
    onUpdateField(selectedElementId, stripUndefined(next));
    // Defer field-state writes until after the current input event has
    // finished propagating. setFieldsValue mid-event tends to steal focus
    // from the input the user is typing into.
    if (pendingNameSync !== null || pendingRequiredSync) {
      queueMicrotask(() => {
        const patch: Record<string, unknown> = {};
        if (pendingNameSync !== null) {
          patch.name = pendingNameSync;
        }
        if (pendingRequiredSync) {
          patch.required = false;
        }
        form.setFieldsValue(patch as Parameters<typeof form.setFieldsValue>[0]);
      });
    }
  };

  return (
    <div style={panelStyle} data-testid="field-properties-panel">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          marginBottom: 16,
        }}
      >
        <h3 style={{ margin: 0 }}>{componentType} field</h3>
        <Button
          type="text"
          icon={<Icons.TrashCan />}
          onClick={handleRemoveClick}
          aria-label="Remove field"
          data-testid="remove-field-button"
        />
      </div>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={element.props}
      >
        <Form.Item label="Label" name="label" rules={[{ required: true }]}>
          <Input data-testid="prop-label" />
        </Form.Item>
        <Form.Item
          label="Name"
          name="name"
          tooltip="Field key sent to the backend. Auto-generated from the label until you edit it. snake_case, ≤ 64 chars."
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
        <Form.Item
          label="Placeholder"
          name="placeholder"
          tooltip="Hint text shown inside the empty input. Currently shown in the builder preview only — the privacy center backend will need a schema update before it reaches end users."
        >
          <Input data-testid="prop-placeholder" />
        </Form.Item>

        {componentType === "Text" && (
          <>
            <Form.Item label="Default value" name="default_value">
              <Input data-testid="prop-default-value" />
            </Form.Item>
            <Form.Item
              label="Query param key"
              name="query_param_key"
              tooltip="If set, this field's default value is read from the matching URL query parameter."
            >
              <Input data-testid="prop-query-param-key" />
            </Form.Item>
            <Form.Item
              noStyle
              shouldUpdate={(prev, next) => prev.hidden !== next.hidden}
            >
              {({ getFieldValue }) => {
                const hiddenOn = !!getFieldValue("hidden");
                return (
                  <Form.Item
                    label="Required"
                    name="required"
                    valuePropName="checked"
                    tooltip={
                      hiddenOn
                        ? "Hidden fields can't be required — the user can't see them to fill them in. Toggle Hidden off first."
                        : "Whether the user must fill this field before submitting."
                    }
                  >
                    <Switch data-testid="prop-required" disabled={hiddenOn} />
                  </Form.Item>
                );
              }}
            </Form.Item>
            <Form.Item
              label="Hidden"
              name="hidden"
              valuePropName="checked"
              tooltip="Hide this field on the privacy center form. Useful for query-param-driven values."
            >
              <Switch data-testid="prop-hidden" />
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
            <Form.Item
              label="Required"
              name="required"
              valuePropName="checked"
              tooltip="Whether the user must fill this field before submitting."
            >
              <Switch data-testid="prop-required" />
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
              <OptionsEditor minItems={0} />
            </Form.Item>
            <Form.Item
              label="IP geolocation hint"
              name="ip_geolocation_hint"
              valuePropName="checked"
              tooltip="Pre-fill the location based on the user's IP address (best-effort)."
            >
              <Switch data-testid="prop-ip-hint" />
            </Form.Item>
            <Form.Item
              label="Required"
              name="required"
              valuePropName="checked"
              tooltip="Whether the user must fill this field before submitting."
            >
              <Switch data-testid="prop-required" />
            </Form.Item>
          </>
        )}
      </Form>
    </div>
  );
};
