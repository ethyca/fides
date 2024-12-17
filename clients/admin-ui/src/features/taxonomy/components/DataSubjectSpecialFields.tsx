import {
  AntCheckbox as Checkbox,
  AntForm as Form,
  AntSelect as Select,
} from "fidesui";
import { isEmpty } from "lodash";

import { enumToOptions } from "~/features/common/helpers";
import { DataSubjectRightsEnum, IncludeExcludeEnum } from "~/types/api";

const DataSubjectSpecialFields = () => {
  const form = Form.useFormInstance();
  const rightsValues = Form.useWatch(["rights", "values"], form);

  return (
    <>
      <Form.Item<boolean>
        label="Automated Decisions or Profiling"
        name="automated_decisions_or_profiling"
        layout="horizontal"
        valuePropName="checked"
      >
        <Checkbox data-testid="edit-taxonomy-form_automated-decisions" />
      </Form.Item>
      <Form.Item<string[]> name={["rights", "values"]} label="Rights">
        <Select
          mode="multiple"
          options={enumToOptions(DataSubjectRightsEnum)}
          data-testid="edit-taxonomy-form_rights"
        />
      </Form.Item>
      {rightsValues && !isEmpty(rightsValues) && (
        <Form.Item<string>
          name={["rights", "strategy"]}
          label="Strategy"
          required
          rules={[{ required: true, message: "Please select a strategy" }]}
        >
          <Select
            options={enumToOptions(IncludeExcludeEnum)}
            data-testid="edit-taxonomy-form_strategy"
          />
        </Form.Item>
      )}
    </>
  );
};
export default DataSubjectSpecialFields;
