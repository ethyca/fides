import { AntForm, AntInput } from "fidesui";
import { isEmpty, unset } from "lodash";

import { FormValues, TaxonomyEntity } from "../types";
import { DefaultTaxonomyTypes } from "../types/DefaultTaxonomyTypes";
import DataSubjectSpecialFields from "./DataSubjectSpecialFields";
import TaxonomyCustomFields from "./TaxonomyCustomFields";

interface TaxonomyEditFormProps {
  initialValues: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  taxonomyType: DefaultTaxonomyTypes;
}

const TaxonomyEditForm = ({
  initialValues,
  onSubmit,
  formId,
  taxonomyType,
}: TaxonomyEditFormProps) => {
  const [form] = AntForm.useForm();

  const handleFinish = (formValues: FormValues) => {
    const updatedTaxonomy: TaxonomyEntity = {
      ...initialValues,
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

      {isDataSubjectType && <DataSubjectSpecialFields />}
      <TaxonomyCustomFields
        fidesKey={initialValues.fides_key}
        taxonomyType={taxonomyType}
      />
    </AntForm>
  );
};
export default TaxonomyEditForm;
