import { AntForm, AntFormInstance, AntInput } from "fidesui";
import { isEmpty, unset } from "lodash";

import { FormValues, TaxonomyEntity } from "../types";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";
import DataSubjectSpecialFields from "./DataSubjectSpecialFields";

interface TaxonomyEditFormProps {
  initialValues: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  form: AntFormInstance;
  taxonomyType: CoreTaxonomiesEnum;
}

const TaxonomyEditForm = ({
  initialValues,
  onSubmit,
  form,
  formId,
  taxonomyType,
}: TaxonomyEditFormProps) => {
  const handleFinish = (formValues: FormValues) => {
    const updatedTaxonomy: TaxonomyEntity = {
      ...initialValues,
      ...formValues,
    };
    if (
      !updatedTaxonomy?.rights?.values ||
      isEmpty(updatedTaxonomy?.rights?.values)
    ) {
      unset(updatedTaxonomy, "rights");
    }
    onSubmit(updatedTaxonomy);
  };

  const isDataSubjectType = taxonomyType === CoreTaxonomiesEnum.DATA_SUBJECTS;

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
    </AntForm>
  );
};
export default TaxonomyEditForm;
