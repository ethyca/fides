import { Form, Select } from "fidesui";

import { DataCategory } from "~/types/api";

interface DataCategoriesFormItemProps {
  allDataCategories: DataCategory[];
  disabled?: boolean;
  required?: boolean;
  tooltip?: string;
}

const DEFAULT_TOOLTIP =
  "What type of data is your system processing? This could be various types of user or system data.";

export const DataCategoriesFormItem = ({
  allDataCategories,
  disabled,
  required,
  tooltip = DEFAULT_TOOLTIP,
}: DataCategoriesFormItemProps) => (
  <Form.Item
    name="data_categories"
    label="Data categories"
    tooltip={tooltip}
    rules={
      required
        ? [
            {
              required: true,
              type: "array",
              min: 1,
              message: "Must assign at least one data category",
            },
          ]
        : undefined
    }
  >
    <Select
      aria-label="Data categories"
      mode="multiple"
      data-testid="input-data_categories"
      disabled={disabled}
      options={allDataCategories.map((dc) => ({
        value: dc.fides_key,
        label: dc.fides_key,
      }))}
      showSearch
      optionFilterProp="label"
    />
  </Form.Item>
);
