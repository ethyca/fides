import {
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput,
} from "fidesui";
import { isEmpty, unset } from "lodash";

import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { FormValues, TaxonomyEntity } from "~/features/taxonomy/types";

import DataSubjectSpecialFields from "./DataSubjectSpecialFields";
import SystemGroupEditForm from "./SystemGroupEditForm";

interface TaxonomyEditFormProps {
  initialValues: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  form: FormInstance;
  taxonomyType: string;
  isDisabled?: boolean;
}

const TaxonomyEditForm = ({
  initialValues,
  onSubmit,
  form,
  formId,
  taxonomyType,
  isDisabled,
}: TaxonomyEditFormProps) => {
  const isDataSubjectType = taxonomyType === TaxonomyTypeEnum.DATA_SUBJECT;
  const isSystemGroupType = taxonomyType === TaxonomyTypeEnum.SYSTEM_GROUP;

  // For system groups, use the dedicated SystemGroupEditForm
  if (isSystemGroupType) {
    return (
      <SystemGroupEditForm
        initialValues={initialValues}
        onSubmit={onSubmit}
        form={form}
        formId={formId}
        isDisabled={isDisabled}
      />
    );
  }

  // Standard taxonomy form logic
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

  return (
    <Form
      name={formId}
      initialValues={initialValues}
      onFinish={handleFinish}
      layout="vertical"
      form={form}
    >
      <Form.Item<string> label="Name" name="name">
        <AntInput data-testid="edit-taxonomy-form_name" disabled={isDisabled} />
      </Form.Item>
      <Form.Item<string> label="Description" name="description">
        <AntInput.TextArea
          rows={4}
          data-testid="edit-taxonomy-form_description"
          disabled={isDisabled}
        />
      </Form.Item>

      {isDataSubjectType && <DataSubjectSpecialFields />}
    </Form>
  );
};
export default TaxonomyEditForm;
