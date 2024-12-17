import {
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput,
} from "fidesui";
import { isEmpty, unset } from "lodash";

import { CoreTaxonomiesEnum } from "../constants";
import { FormValues, TaxonomyEntity } from "../types";
import DataSubjectSpecialFields from "./DataSubjectSpecialFields";

interface TaxonomyEditFormProps {
  initialValues: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  form: FormInstance;
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
    <Form
      name={formId}
      initialValues={initialValues}
      onFinish={handleFinish}
      layout="vertical"
      form={form}
    >
      <Form.Item<string> label="Name" name="name">
        <AntInput data-testid="edit-taxonomy-form_name" />
      </Form.Item>
      <Form.Item<string> label="Description" name="description">
        <AntInput.TextArea
          rows={4}
          data-testid="edit-taxonomy-form_description"
        />
      </Form.Item>

      {isDataSubjectType && <DataSubjectSpecialFields />}
    </Form>
  );
};
export default TaxonomyEditForm;
