import { Form, Input, InputNumber, Select, Switch } from "fidesui";

export const DATA_TYPE_OPTIONS = [
  "string",
  "integer",
  "float",
  "boolean",
  "object_id",
  "object",
].map((v) => ({ label: v, value: v }));

export const REDACT_OPTIONS = [
  { label: "None", value: "" },
  { label: "name", value: "name" },
];

/**
 * Build a fides_meta object from flat form values, using undefined for empty
 * values so JSON.stringify drops them on save.
 */
export const buildFieldMeta = (values: Record<string, unknown>) => {
  const redactVal = values.redact as string;
  const meta = {
    data_type: (values.data_type as string) || undefined,
    identity: (values.identity as string) || undefined,
    primary_key: (values.primary_key as boolean) || undefined,
    read_only: (values.read_only as boolean) || undefined,
    return_all_elements: (values.return_all_elements as boolean) || undefined,
    length:
      values.length !== null &&
      values.length !== undefined &&
      values.length !== ""
        ? (values.length as number)
        : undefined,
    custom_request_field: (values.custom_request_field as string) || undefined,
    redact: redactVal === "name" ? ("name" as const) : undefined,
  };
  const hasAny = Object.values(meta).some((v) => v !== undefined);
  return hasAny ? meta : undefined;
};

/**
 * Shared Form.Item components for field-level fides_meta editing.
 * Expects to be rendered inside an Ant Design <Form>.
 */
const FieldMetadataFormItems = () => (
  <>
    <Form.Item label="Data Type" name="data_type">
      <Select
        allowClear
        placeholder="Select data type..."
        aria-label="Data Type"
        options={DATA_TYPE_OPTIONS}
      />
    </Form.Item>
    <Form.Item label="Identity" name="identity">
      <Input placeholder="e.g. email, phone_number" />
    </Form.Item>
    <Form.Item label="Primary Key" name="primary_key" valuePropName="checked">
      <Switch aria-label="Primary Key" />
    </Form.Item>
    <Form.Item label="Read Only" name="read_only" valuePropName="checked">
      <Switch aria-label="Read Only" />
    </Form.Item>
    <Form.Item
      label="Return All Elements"
      name="return_all_elements"
      valuePropName="checked"
    >
      <Switch aria-label="Return All Elements" />
    </Form.Item>
    <Form.Item label="Length" name="length">
      <InputNumber min={0} placeholder="Max length" style={{ width: "100%" }} />
    </Form.Item>
    <Form.Item label="Custom Request Field" name="custom_request_field">
      <Input placeholder="Custom field name" />
    </Form.Item>
    <Form.Item label="Redact" name="redact">
      <Select aria-label="Redact" options={REDACT_OPTIONS} />
    </Form.Item>
  </>
);

export default FieldMetadataFormItems;
