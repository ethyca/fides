import {
  Button,
  Card,
  Checkbox,
  Flex,
  Form,
  Icons,
  Input,
  Select,
  Typography,
} from "fidesui";
import { useEffect, useMemo } from "react";

import { useGetPoliciesQuery } from "~/features/policies/policy.slice";
import type {
  fides__api__schemas__privacy_center_config__PrivacyCenterConfig as PrivacyCenterConfig,
  PrivacyRequestOption,
} from "~/types/api";

import { DEFAULT_PRIVACY_CENTER_CONFIG } from "../privacy-center/helpers";

export type PrivacyCenterConfigValue = PrivacyCenterConfig;

const IDENTITY_KEYS = ["email", "phone"] as const;

const FIELD_TYPE_OPTIONS = [
  { value: "location", label: "Location" },
  { value: "text", label: "Text" },
  { value: "select", label: "Select" },
  { value: "multiselect", label: "Multi-select" },
];

interface CustomFieldEntry {
  key: string;
  field_type?: string | null;
  label: string;
  required?: boolean | null;
  hidden?: boolean | null;
  ip_geolocation_hint?: boolean | null;
  default_value?: string | null;
  options?: string[] | null;
}

const DEFAULT_CUSTOM_FIELD: CustomFieldEntry = {
  key: "",
  field_type: "text",
  label: "",
  required: true,
  hidden: false,
};

const DEFAULT_ACTION: PrivacyRequestOption = {
  icon_path: "",
  title: "",
  description: "",
  confirmButtonText: "Continue",
  cancelButtonText: "Cancel",
  identity_inputs: { email: "required" },
  custom_privacy_request_fields: {},
};

interface Props {
  value: PrivacyCenterConfigValue | null;
  onChange?: (next: PrivacyCenterConfigValue) => void;
}

// Controlled component bound to Form.Item name={[name, "identity_inputs"]}.
// Form.Item injects value/onChange; the component owns only rendering logic.
const IdentityInputsField = ({
  actionIndex,
  value = {},
  onChange,
}: {
  actionIndex: number;
  value?: Record<string, string>;
  onChange?: (val: Record<string, string>) => void;
}) => {
  const handleToggle = (key: string, checked: boolean) => {
    const updated = { ...value };
    if (checked) {
      updated[key] = "required";
    } else {
      delete updated[key];
    }
    onChange?.(updated);
  };

  const handleRequired = (key: string, required: boolean) => {
    onChange?.({ ...value, [key]: required ? "required" : "optional" });
  };

  return (
    <Flex vertical gap="small">
      {IDENTITY_KEYS.map((key) => {
        const isEnabled = key in value;
        const isRequired = value[key] === "required";
        return (
          <Flex key={key} gap="small" align="center">
            <Checkbox
              checked={isEnabled}
              onChange={(e) => handleToggle(key, e.target.checked)}
              data-testid={`identity-${key}-enabled-${actionIndex}`}
            >
              <span className="capitalize">{key}</span>
            </Checkbox>
            <Checkbox
              checked={isRequired}
              disabled={!isEnabled}
              onChange={(e) => handleRequired(key, e.target.checked)}
              data-testid={`identity-${key}-required-${actionIndex}`}
            >
              Required
            </Checkbox>
          </Flex>
        );
      })}
    </Flex>
  );
};

// Controlled component bound to Form.Item name={[name, "custom_privacy_request_fields"]}.
const CustomFieldsEditor = ({
  actionIndex,
  value = {},
  onChange,
}: {
  actionIndex: number;
  value?: Record<string, Omit<CustomFieldEntry, "key">>;
  onChange?: (val: Record<string, unknown>) => void;
}) => {
  const entries: CustomFieldEntry[] = Object.entries(value).map(
    ([key, val]) => ({ key, ...val }),
  );

  const sync = (updated: CustomFieldEntry[]) => {
    const dict: Record<string, unknown> = {};
    updated.forEach(({ key, ...rest }) => {
      if (key) {
        dict[key] = rest;
      }
    });
    onChange?.(dict);
  };

  const handleAdd = () =>
    sync([
      ...entries,
      { ...DEFAULT_CUSTOM_FIELD, key: `field_${entries.length + 1}` },
    ]);

  const handleRemove = (index: number) =>
    sync(entries.filter((_, i) => i !== index));

  const handleChange = (
    index: number,
    field: keyof CustomFieldEntry,
    val: unknown,
  ) =>
    sync(
      entries.map((entry, i) =>
        i === index ? { ...entry, [field]: val } : entry,
      ),
    );

  const handleAddOption = (entryIndex: number) => {
    const current = entries[entryIndex].options ?? [];
    handleChange(entryIndex, "options", [...current, ""]);
  };

  const handleRemoveOption = (entryIndex: number, optionIndex: number) => {
    const updated = (entries[entryIndex].options ?? []).filter(
      (_, i) => i !== optionIndex,
    );
    handleChange(entryIndex, "options", updated.length ? updated : null);
  };

  const handleOptionChange = (
    entryIndex: number,
    optionIndex: number,
    val: string,
  ) => {
    const updated = (entries[entryIndex].options ?? []).map((opt, i) =>
      i === optionIndex ? val : opt,
    );
    handleChange(entryIndex, "options", updated);
  };

  return (
    <Flex vertical gap="small">
      {entries.map((entry, index) => {
        const isLocation = entry.field_type === "location";
        const hasOptions =
          entry.field_type === "select" || entry.field_type === "multiselect";
        const showDefaultValue = !!entry.hidden || hasOptions;
        return (
          <Card
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            size="small"
            extra={
              <Button
                aria-label="Remove custom field"
                icon={<Icons.TrashCan />}
                onClick={() => handleRemove(index)}
                data-testid={`remove-custom-field-${actionIndex}-${index}`}
              />
            }
            title={
              <Typography.Text type="secondary">
                {`Custom field ${index + 1}${entry.label ? ` — ${entry.label}` : ""}`}
              </Typography.Text>
            }
            data-testid={`custom-field-${actionIndex}-${index}`}
          >
            <Flex vertical gap="small">
              <Form.Item label="Field key (internal name)" className="!mb-0">
                <Input
                  value={entry.key}
                  onChange={(e) => handleChange(index, "key", e.target.value)}
                  size="small"
                  data-testid={`custom-field-key-${actionIndex}-${index}`}
                />
              </Form.Item>
              <Form.Item label="Field type" className="!mb-0">
                <Select
                  aria-label="Field type"
                  value={entry.field_type ?? "text"}
                  options={FIELD_TYPE_OPTIONS}
                  onChange={(val) => handleChange(index, "field_type", val)}
                  data-testid={`custom-field-type-${actionIndex}-${index}`}
                />
              </Form.Item>
              <Form.Item label="Label" className="!mb-0">
                <Input
                  value={entry.label}
                  onChange={(e) => handleChange(index, "label", e.target.value)}
                  size="small"
                  data-testid={`custom-field-label-${actionIndex}-${index}`}
                />
              </Form.Item>
              <Flex gap="small">
                <Checkbox
                  checked={!!entry.required}
                  onChange={(e) =>
                    handleChange(index, "required", e.target.checked)
                  }
                  data-testid={`custom-field-required-${actionIndex}-${index}`}
                >
                  Required
                </Checkbox>
                {!isLocation && (
                  <Checkbox
                    checked={!!entry.hidden}
                    onChange={(e) =>
                      handleChange(index, "hidden", e.target.checked)
                    }
                    data-testid={`custom-field-hidden-${actionIndex}-${index}`}
                  >
                    Hidden
                  </Checkbox>
                )}
                {isLocation && (
                  <Checkbox
                    checked={!!entry.ip_geolocation_hint}
                    onChange={(e) =>
                      handleChange(
                        index,
                        "ip_geolocation_hint",
                        e.target.checked,
                      )
                    }
                    data-testid={`custom-field-ip-hint-${actionIndex}-${index}`}
                  >
                    IP geolocation hint
                  </Checkbox>
                )}
              </Flex>
              {showDefaultValue && (
                <Form.Item
                  label={`Default value${entry.hidden ? " (required when hidden)" : ""}`}
                  className="!mb-0"
                >
                  <Input
                    value={entry.default_value ?? ""}
                    onChange={(e) =>
                      handleChange(index, "default_value", e.target.value)
                    }
                    size="small"
                    data-testid={`custom-field-default-${actionIndex}-${index}`}
                  />
                </Form.Item>
              )}
              {hasOptions && (
                <Form.Item label="Options" className="!mb-0">
                  <Flex vertical gap={4}>
                    {(entry.options ?? []).map((opt, optIdx) => (
                      // eslint-disable-next-line react/no-array-index-key
                      <Flex key={optIdx} gap="small" align="center">
                        <Input
                          value={opt}
                          onChange={(e) =>
                            handleOptionChange(index, optIdx, e.target.value)
                          }
                          size="small"
                          data-testid={`custom-field-option-${actionIndex}-${index}-${optIdx}`}
                        />
                        <Button
                          aria-label="Remove option"
                          icon={<Icons.TrashCan />}
                          onClick={() => handleRemoveOption(index, optIdx)}
                          data-testid={`remove-option-${actionIndex}-${index}-${optIdx}`}
                        />
                      </Flex>
                    ))}
                    <div>
                      <Button
                        icon={<Icons.Add />}
                        onClick={() => handleAddOption(index)}
                        data-testid={`add-option-${actionIndex}-${index}`}
                      >
                        Add option
                      </Button>
                    </div>
                  </Flex>
                </Form.Item>
              )}
            </Flex>
          </Card>
        );
      })}
      <div>
        <Button
          icon={<Icons.Add />}
          onClick={handleAdd}
          data-testid={`add-custom-field-${actionIndex}`}
        >
          Add custom field
        </Button>
      </div>
    </Flex>
  );
};

const ActionCard = ({ name }: { name: number }) => {
  const { data: policiesPage } = useGetPoliciesQuery();

  const policyOptions = useMemo(
    () =>
      (policiesPage?.items ?? []).map((p) => ({
        value: p.key ?? "",
        label: p.name,
      })),
    [policiesPage],
  );

  return (
    <>
      <Form.Item name={[name, "policy_key"]} label="Policy key">
        <Select
          aria-label="Policy key"
          options={policyOptions}
          allowClear
          placeholder="Select policy"
          data-testid={`action-policy-key-${name}`}
        />
      </Form.Item>
      <Form.Item name={[name, "icon_path"]} label="Icon path">
        <Input
          placeholder="https://example.com/icon.svg"
          data-testid={`action-icon-path-${name}`}
        />
      </Form.Item>
      <Form.Item
        name={[name, "title"]}
        label="Title"
        rules={[{ required: true, message: "Title is required" }]}
      >
        <Input data-testid={`action-title-${name}`} />
      </Form.Item>
      <Form.Item
        name={[name, "description"]}
        label="Description"
        rules={[{ required: true, message: "Description is required" }]}
      >
        <Input data-testid={`action-description-${name}`} />
      </Form.Item>
      <Form.Item name={[name, "confirmButtonText"]} label="Confirm button text">
        <Input data-testid={`action-confirm-text-${name}`} />
      </Form.Item>
      <Form.Item name={[name, "cancelButtonText"]} label="Cancel button text">
        <Input data-testid={`action-cancel-text-${name}`} />
      </Form.Item>
      <Form.Item name={[name, "identity_inputs"]} label="Identity inputs">
        <IdentityInputsField actionIndex={name} />
      </Form.Item>
      <Form.Item
        name={[name, "custom_privacy_request_fields"]}
        label="Custom fields"
        className="!mb-0"
      >
        <CustomFieldsEditor actionIndex={name} />
      </Form.Item>
    </>
  );
};

export const PrivacyCenterConfigSection = ({ value, onChange }: Props) => {
  const [form] = Form.useForm<PrivacyCenterConfigValue>();

  useEffect(() => {
    if (value) {
      form.setFieldsValue(value as Parameters<typeof form.setFieldsValue>[0]);
    }
  }, [value, form]);

  const initialValues = useMemo(
    () => value ?? DEFAULT_PRIVACY_CENTER_CONFIG,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const handleValuesChange = () => {
    onChange?.(form.getFieldsValue(true) as PrivacyCenterConfigValue);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues as Parameters<typeof form.setFieldsValue>[0]}
      onValuesChange={handleValuesChange}
    >
      <Flex vertical gap={16}>
        <Card title="General" size="small">
          <Form.Item
            name="title"
            label="Title"
            rules={[{ required: true, message: "Title is required" }]}
          >
            <Input data-testid="pc-config-title" />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: "Description is required" }]}
          >
            <Input data-testid="pc-config-description" />
          </Form.Item>
          <Form.Item name="logo_path" label="Logo path">
            <Input data-testid="pc-config-logo-path" />
          </Form.Item>
          <Form.Item name="logo_url" label="Logo URL">
            <Input data-testid="pc-config-logo-url" />
          </Form.Item>
          <Form.Item name="favicon_path" label="Favicon path">
            <Input data-testid="pc-config-favicon-path" />
          </Form.Item>
          <Form.Item name="privacy_policy_url" label="Privacy policy URL">
            <Input data-testid="pc-config-privacy-policy-url" />
          </Form.Item>
          <Form.Item
            name="privacy_policy_url_text"
            label="Privacy policy URL text"
            className="!mb-0"
          >
            <Input data-testid="pc-config-privacy-policy-url-text" />
          </Form.Item>
        </Card>

        <Card title="Actions" size="small">
          <Form.List name="actions">
            {(fields, { add, remove }) => (
              <Flex vertical gap={12}>
                {fields.map(({ key, name }) => (
                  <Card
                    key={key}
                    size="small"
                    extra={
                      <Button
                        aria-label="Remove action"
                        icon={<Icons.TrashCan />}
                        onClick={() => remove(name)}
                        disabled={fields.length === 1}
                        data-testid={`remove-action-${name}`}
                      />
                    }
                    title={`Action ${name + 1}`}
                  >
                    <ActionCard name={name} />
                  </Card>
                ))}
                <div>
                  <Button
                    icon={<Icons.Add />}
                    onClick={() => add({ ...DEFAULT_ACTION })}
                    data-testid="add-action-button"
                  >
                    Add action
                  </Button>
                </div>
              </Flex>
            )}
          </Form.List>
        </Card>
      </Flex>
    </Form>
  );
};
