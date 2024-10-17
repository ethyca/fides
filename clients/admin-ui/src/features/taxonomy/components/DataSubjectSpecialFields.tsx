import { AntCheckbox, AntForm, AntSelect } from "fidesui";
import { isEmpty } from "lodash";

import { enumToOptions } from "~/features/common/helpers";
import { DataSubjectRightsEnum, IncludeExcludeEnum } from "~/types/api";

const DataSubjectSpecialFields = () => {
  const form = AntForm.useFormInstance();
  const rightsValues = AntForm.useWatch(["rights", "values"], form);

  return (
    <>
      <AntForm.Item<boolean>
        label="Automated Decisions or Profiling"
        name="automated_decisions_or_profiling"
        layout="horizontal"
        valuePropName="checked"
      >
        <AntCheckbox />
      </AntForm.Item>
      <AntForm.Item<string[]> name={["rights", "values"]} label="Rights">
        <AntSelect
          mode="multiple"
          options={enumToOptions(DataSubjectRightsEnum)}
        />
      </AntForm.Item>
      {rightsValues && !isEmpty(rightsValues) && (
        <AntForm.Item<string>
          name={["rights", "strategy"]}
          label="Strategy"
          required
          rules={[{ required: true, message: "Please select a strategy" }]}
        >
          <AntSelect options={enumToOptions(IncludeExcludeEnum)} />
        </AntForm.Item>
      )}
    </>
  );
};
export default DataSubjectSpecialFields;
