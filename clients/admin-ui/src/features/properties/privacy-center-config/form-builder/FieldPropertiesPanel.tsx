import {
  Alert,
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Select,
  Switch,
  Typography,
  useModal,
} from "fidesui";
import snakeCase from "lodash.snakecase";
import { useEffect, useRef, useState } from "react";

import { OptionsEditor } from "./OptionsEditor";
import type {
  EditableType,
  FieldPropertiesPanelProps,
  FormValues,
  JsonRenderSpec,
} from "./types";
import {
  type ConditionRow,
  rowsToVisible,
  VisibilityEditor,
  visibleToRows,
} from "./VisibilityEditor";

const stripUndefined = (
  values: Record<string, unknown>,
): Record<string, unknown> => {
  const result: Record<string, unknown> = {};
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined) {
      result[k] = v;
    }
  });
  return result;
};

const EmptyState = () => (
  <Flex vertical className="h-full overflow-y-auto p-4">
    <Alert type="info" title="Select a field to edit its properties." />
  </Flex>
);

export const FieldPropertiesPanel = ({
  spec,
  selectedElementId,
  onUpdateField,
  onRemoveField,
  onUpdateVisibility,
}: FieldPropertiesPanelProps) => {
  const [form] = Form.useForm<FormValues>();
  const modal = useModal();
  // Auto-sync the field's name from its label until the user manually edits
  // the name. The flag is recomputed on every selection change based on
  // whether the existing name still matches snakeCase(label) — fields with
  // customized names start with auto-sync off.
  const autoSyncNameRef = useRef(true);
  // Visibility-condition rows. Local state mirrors the saved element.visible
  // and is re-synced whenever selection changes.
  const [visibilityRows, setVisibilityRows] = useState<ConditionRow[]>([]);
  // Signature of the props/visible we last synced into the antd form +
  // visibilityRows. Used to detect EXTERNAL spec changes (e.g. the chat
  // agent rewrote the spec) without re-syncing on every local keystroke,
  // which would steal focus from inputs.
  const lastSyncedSignatureRef = useRef<string>("");

  const element = selectedElementId
    ? spec?.elements?.[selectedElementId]
    : null;

  const handleRemoveClick = () => {
    if (!selectedElementId || !element) {
      return;
    }
    const isIdentity =
      element.type === "Email" ||
      element.type === "Name" ||
      element.type === "Phone";
    const fieldName = isIdentity
      ? element.type
      : ((element.props as { name?: string }).name ?? selectedElementId);
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

  // Re-sync the panel from the spec on selection change AND on external
  // spec edits (e.g. the chat agent rewriting the spec while a field is
  // selected). We track a signature of the props+visible that were last
  // synced; if the live element's signature differs, the change came from
  // outside this panel and we re-apply. Local keystrokes update the spec
  // and the ref together, so the signatures stay equal and we don't steal
  // focus.
  useEffect(() => {
    if (!element) {
      lastSyncedSignatureRef.current = "";
      return;
    }
    const { visible } = element as JsonRenderSpec["elements"][string] & {
      visible?: unknown;
    };
    const signature = JSON.stringify({ props: element.props, visible });
    if (signature === lastSyncedSignatureRef.current) {
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
    setVisibilityRows(visibleToRows(visible));
    lastSyncedSignatureRef.current = signature;
  }, [selectedElementId, element, form]);

  const handleVisibilityChange = (next: ConditionRow[]) => {
    setVisibilityRows(next);
    if (selectedElementId) {
      const nextVisible = rowsToVisible(next);
      onUpdateVisibility(selectedElementId, nextVisible);
      // Track the signature we just wrote so the resync effect treats
      // this as a local edit and doesn't re-apply on the next render.
      lastSyncedSignatureRef.current = JSON.stringify({
        props: element?.props ?? {},
        visible: nextVisible,
      });
    }
  };

  if (!element || !selectedElementId) {
    return <EmptyState />;
  }

  const componentType = element.type as EditableType;
  const isIdentityType =
    componentType === "Email" ||
    componentType === "Name" ||
    componentType === "Phone";

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
    // Hidden + visibility conditions also contradict — a hidden field is
    // never shown, so per-condition visibility is moot. Clear any rows
    // when Hidden turns on.
    if (
      "hidden" in changed &&
      changed.hidden === true &&
      visibilityRows.length > 0
    ) {
      setVisibilityRows([]);
      onUpdateVisibility(selectedElementId, undefined);
    }
    const nextProps = stripUndefined(next);
    onUpdateField(selectedElementId, nextProps);
    // Track the signature we just wrote — including any visibility we
    // just cleared — so the resync effect skips local edits.
    const nextVisible =
      "hidden" in changed &&
      changed.hidden === true &&
      visibilityRows.length > 0
        ? undefined
        : (
            element as JsonRenderSpec["elements"][string] & {
              visible?: unknown;
            }
          ).visible;
    lastSyncedSignatureRef.current = JSON.stringify({
      props: nextProps,
      visible: nextVisible,
    });
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
    <Flex
      vertical
      className="h-full overflow-y-auto p-4"
      data-testid="field-properties-panel"
    >
      <Flex align="center" justify="space-between" gap="small" className="mb-4">
        <Typography.Title level={5} className="m-0">
          {componentType} field
        </Typography.Title>
        <Button
          type="text"
          icon={<Icons.TrashCan />}
          onClick={handleRemoveClick}
          aria-label="Remove field"
          data-testid="remove-field-button"
        />
      </Flex>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={element.props}
      >
        {isIdentityType ? (
          <>
            <Alert
              type="info"
              title="Identity field"
              description="This field maps to a built-in privacy center identity input. Its label and field key are fixed and cannot be customized."
              className="mb-4"
            />
            <Form.Item
              label="Required"
              name="required"
              valuePropName="checked"
              tooltip="Whether the user must fill this field before submitting."
            >
              <Switch data-testid="prop-required" />
            </Form.Item>
          </>
        ) : (
          <>
            <Form.Item
              noStyle
              shouldUpdate={(prev, next) => prev.hidden !== next.hidden}
            >
              {({ getFieldValue }) => {
                const hiddenOn = !!getFieldValue("hidden");
                return (
                  <>
                    <Form.Item
                      label="Label"
                      name="label"
                      rules={[{ required: !hiddenOn }]}
                      tooltip={
                        hiddenOn
                          ? "Hidden fields aren't shown to end users, so the label is unused. Toggle Hidden off to edit."
                          : undefined
                      }
                    >
                      <Input data-testid="prop-label" disabled={hiddenOn} />
                    </Form.Item>
                    <Form.Item
                      label="Name"
                      name="name"
                      tooltip="Field key sent to the backend. Auto-generated from the label until you edit it. snake_case, ≤ 64 chars."
                      rules={[
                        {
                          required: true,
                          pattern: /^[a-z][a-z0-9_]{0,63}$/,
                          message:
                            "snake_case, must start with a letter, ≤ 64 chars",
                        },
                      ]}
                    >
                      <Input data-testid="prop-name" />
                    </Form.Item>
                    <Form.Item
                      label="Placeholder"
                      name="placeholder"
                      tooltip={
                        hiddenOn
                          ? "Hidden fields aren't rendered, so placeholder text isn't shown. Toggle Hidden off to edit."
                          : "Hint text shown inside the empty input."
                      }
                    >
                      <Input
                        data-testid="prop-placeholder"
                        disabled={hiddenOn}
                      />
                    </Form.Item>
                  </>
                );
              }}
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
                        <Switch
                          data-testid="prop-required"
                          disabled={hiddenOn}
                        />
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

            {(componentType === "Select" ||
              componentType === "MultiSelect" ||
              componentType === "Radio") && (
              <>
                <Form.Item
                  label="Options"
                  name="options"
                  rules={[{ required: true, message: "At least one option" }]}
                >
                  <OptionsEditor />
                </Form.Item>
                <Form.Item
                  noStyle
                  shouldUpdate={(prev, next) =>
                    JSON.stringify(prev.options) !==
                    JSON.stringify(next.options)
                  }
                >
                  {({ getFieldValue }) => {
                    const opts = (getFieldValue("options") ?? []) as string[];
                    const isMulti = componentType === "MultiSelect";
                    return (
                      <Form.Item label="Default value" name="default_value">
                        <Select
                          aria-label="Default value"
                          mode={isMulti ? "multiple" : undefined}
                          allowClear
                          placeholder="No default"
                          data-testid="prop-default-value"
                          options={opts.map((o) => ({ label: o, value: o }))}
                        />
                      </Form.Item>
                    );
                  }}
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
            <Form.Item
              noStyle
              shouldUpdate={(prev, next) => prev.hidden !== next.hidden}
            >
              {({ getFieldValue }) => {
                const hiddenOn = !!getFieldValue("hidden");
                return (
                  <Form.Item
                    label="Visibility"
                    tooltip={
                      hiddenOn
                        ? "Hidden fields can't have visibility conditions — the field is never shown to end users. Toggle Hidden off first."
                        : "Show this field only when conditions are met."
                    }
                  >
                    {hiddenOn ? (
                      <Alert
                        type="info"
                        title="Visibility conditions are unavailable while this field is hidden."
                      />
                    ) : (
                      <VisibilityEditor
                        spec={spec}
                        selectedElementId={selectedElementId}
                        rows={visibilityRows}
                        onChange={handleVisibilityChange}
                      />
                    )}
                  </Form.Item>
                );
              }}
            </Form.Item>
          </>
        )}
      </Form>
    </Flex>
  );
};
