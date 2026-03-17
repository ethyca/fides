import { Form, Input, InputNumber, Select, Switch } from "fidesui";
import { useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const BASE_DATA_TYPES = [
  "string",
  "integer",
  "float",
  "boolean",
  "object_id",
  "object",
];

export const DATA_TYPE_OPTIONS = [
  ...BASE_DATA_TYPES,
  ...BASE_DATA_TYPES.map((t) => `${t}[]`),
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
 * A Select with mode="tags" that suggests known data categories from the
 * taxonomy while still allowing free-form input.
 */
export const DataCategoryTagSelect = ({
  value,
  onChange,
}: {
  value?: string[];
  onChange?: (value: string[]) => void;
}) => {
  const { getDataCategories } = useTaxonomies();
  const options = useMemo(
    () =>
      getDataCategories()
        .filter((c) => c.active)
        .map((c) => ({ label: c.fides_key, value: c.fides_key })),
    [getDataCategories],
  );

  return (
    <Select
      mode="tags"
      placeholder="Add data categories..."
      aria-label="Data Categories"
      style={{ width: "100%" }}
      options={options}
      value={value}
      onChange={onChange}
      filterOption={(input, option) =>
        (option?.value as string)
          ?.toLowerCase()
          .includes(input.toLowerCase()) ?? false
      }
    />
  );
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
