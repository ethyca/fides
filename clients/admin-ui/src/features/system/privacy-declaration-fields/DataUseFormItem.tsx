import { Form, Select } from "fidesui";

import { DataUse } from "~/types/api";

interface DataUseFormItemProps {
  allDataUses: DataUse[];
  disabled?: boolean;
}

export const DataUseFormItem = ({
  allDataUses,
  disabled,
}: DataUseFormItemProps) => (
  <Form.Item
    name="data_use"
    label="Data use"
    tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
    rules={[{ required: true, message: "Data use is required" }]}
  >
    <Select
      aria-label="Data use"
      data-testid="input-data_use"
      disabled={disabled}
      options={allDataUses.map((du) => ({
        value: du.fides_key,
        label: du.fides_key,
      }))}
      showSearch
      optionFilterProp="label"
    />
  </Form.Item>
);
