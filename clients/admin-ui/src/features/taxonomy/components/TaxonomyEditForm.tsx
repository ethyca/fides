import { AntCheckbox, AntForm, AntInput, AntSelect } from "fidesui";

import { enumToOptions } from "~/features/common/helpers";
import { DataSubjectRightsEnum } from "~/types/api";

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
  const initialValues = {
    name: values.name ?? "",
    description: values.description ?? "",
    automated_decisions_or_profiling:
      values.automated_decisions_or_profiling ?? false,
  };

  const handleFinish = (formValues: FormValues) => {
    console.log("formValues", formValues);
    const updatedTaxonomy: TaxonomyEntity = {
      ...values,
      ...formValues,
    };
    onSubmit(updatedTaxonomy);
  };

  // TODO: Reimplement custom fields
  // TODO: Reimplement special fields for data subject
  const isDataSubjectType = taxonomyType === "data_subjects";

  console.log(
    "enumToOptions(DataSubjectRightsEnum)",
    enumToOptions(DataSubjectRightsEnum),
  );

  return (
    <AntForm
      name={formId}
      initialValues={initialValues}
      onFinish={handleFinish}
      layout="vertical"
    >
      <AntForm.Item<string>
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please input the taxonomy name" }]}
      >
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
          <AntForm.Item<string[]> label="Rights">
            <AntSelect
              mode="multiple"
              options={enumToOptions(DataSubjectRightsEnum)}
            />
          </AntForm.Item>
        </>
      )}
    </AntForm>
  );
};
export default TaxonomyEditForm;
