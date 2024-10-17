import { AntCheckbox, AntForm, AntInput, AntSelect } from "fidesui";
import { isEmpty, unset } from "lodash";

import { enumToOptions } from "~/features/common/helpers";
import { DataSubjectRightsEnum, IncludeExcludeEnum } from "~/types/api";

import { FormValues, TaxonomyEntity } from "../types";
import { DefaultTaxonomyTypes } from "../types/DefaultTaxonomyTypes";

interface TaxonomyEditFormProps {
  values: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  taxonomyType: DefaultTaxonomyTypes;
}

const TaxonomyEditForm = ({
  values,
  onSubmit,
  formId,
  taxonomyType,
}: TaxonomyEditFormProps) => {
  const [form] = AntForm.useForm();

  const initialValues = values;

  const handleFinish = (formValues: FormValues) => {
    const updatedTaxonomy: TaxonomyEntity = {
      ...values,
      ...formValues,
    };
    if (
      updatedTaxonomy?.rights?.values &&
      isEmpty(updatedTaxonomy?.rights?.values)
    ) {
      unset(updatedTaxonomy, "rights");
    }
    onSubmit(updatedTaxonomy);
  };

  // TODO: Reimplement custom fields
  // TODO: Reimplement special fields for data subject
  const isDataSubjectType = taxonomyType === "data_subjects";
  const rightsValues = AntForm.useWatch(["rights", "values"], form);

  return (
    <AntForm
      name={formId}
      initialValues={initialValues}
      onFinish={handleFinish}
      layout="vertical"
      form={form}
    >
      <AntForm.Item<string> label="Name" name="name">
        <AntInput />
      </AntForm.Item>
      <AntForm.Item<string> label="Description" name="description">
        <AntInput.TextArea rows={4} />
      </AntForm.Item>

      {/* Data Subject only fields */}
      {isDataSubjectType && (
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
      )}
    </AntForm>
  );
};
export default TaxonomyEditForm;
