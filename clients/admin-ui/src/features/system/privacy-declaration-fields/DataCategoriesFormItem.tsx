import { Form, Select } from "fidesui";

import { DataCategory } from "~/types/api";

interface DataCategoriesFormItemProps {
  allDataCategories: DataCategory[];
  disabled?: boolean;
}

export const DataCategoriesFormItem = ({
  allDataCategories,
  disabled,
}: DataCategoriesFormItemProps) => (
  <Form.Item
    name="data_categories"
    label="Data categories"
    tooltip="What type of data is your system processing? This could be various types of user or system data."
    rules={[
      {
        validator: (_, value: string[] | undefined) =>
          value && value.length > 0
            ? Promise.resolve()
            : Promise.reject(
                new Error("Must assign at least one data category"),
              ),
      },
    ]}
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
