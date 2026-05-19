import { Form, Select } from "fidesui";

import { DataSubject } from "~/types/api";

interface DataSubjectsFormItemProps {
  allDataSubjects: DataSubject[];
  disabled?: boolean;
  required?: boolean;
}

export const DataSubjectsFormItem = ({
  allDataSubjects,
  disabled,
  required,
}: DataSubjectsFormItemProps) => (
  <Form.Item
    name="data_subjects"
    label="Data subjects"
    tooltip="Whose data are you processing? This could be customers, employees or any other type of user in your system."
    rules={
      required
        ? [
            {
              validator: (_, value: string[] | undefined) =>
                value && value.length > 0
                  ? Promise.resolve()
                  : Promise.reject(
                      new Error("Must assign at least one data subject"),
                    ),
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
