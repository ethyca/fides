import { AntForm, AntInput } from "fidesui";

import { FormValues, TaxonomyEntity } from "../types";

interface TaxonomyEditFormProps {
  values: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
}

const TaxonomyEditForm = ({
  values,
  onSubmit,
  formId,
}: TaxonomyEditFormProps) => {
  const initialValues = {
    name: values.name ?? "",
    description: values.description ?? "",
  };

  const handleFinish = (formValues: FormValues) => {
    const updatedTaxonomy: TaxonomyEntity = {
      ...values,
      ...formValues,
    };
    onSubmit(updatedTaxonomy);
  };

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
    </AntForm>
  );
};
export default TaxonomyEditForm;
