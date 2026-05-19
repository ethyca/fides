import { Form, Select } from "fidesui";

import { DataSubject } from "~/types/api";

interface DataSubjectsFormItemProps {
  allDataSubjects: DataSubject[];
  disabled?: boolean;
  required?: boolean;
  tooltip?: string;
}

const DEFAULT_TOOLTIP =
  "Whose data are you processing? This could be customers, employees or any other type of user in your system.";

export const DataSubjectsFormItem = ({
  allDataSubjects,
  disabled,
  required,
  tooltip = DEFAULT_TOOLTIP,
}: DataSubjectsFormItemProps) => (
  <Form.Item
    name="data_subjects"
    label="Data subjects"
    tooltip={tooltip}
    rules={
      required
        ? [
            {
              required: true,
              type: "array",
              min: 1,
              message: "Must assign at least one data subject",
            },
          ]
        : undefined
    }
  >
    <Select
      aria-label="Data subjects"
      mode="multiple"
      data-testid="input-data_subjects"
      disabled={disabled}
      options={allDataSubjects.map((ds) => ({
        value: ds.fides_key,
        label: ds.fides_key,
      }))}
      showSearch
      optionFilterProp="label"
    />
  </Form.Item>
);
