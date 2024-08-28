import { Stack } from "fidesui";
import { Form, Formik } from "formik";

import { Dataset } from "~/types/api";

import { CustomTextInput } from "../common/form/inputs";
import { DATASET } from "./constants";

export const FORM_ID = "edit-field-drawer";

type FormValues = Partial<Dataset>;

interface Props {
  values: FormValues;
  onSubmit: (values: FormValues) => void;
}

const EditDatasetForm = ({ values, onSubmit }: Props) => {
  const initialValues: FormValues = {
    name: values.name ?? "",
    description: values.description ?? "",
    data_categories: values.data_categories,
  };

  const handleSubmit = (formValues: FormValues) => {
    // data categories need to be handled separately since they are not a typical form element
    const newValues = {
      ...formValues,
      data_categories: values.data_categories || [],
    };
    onSubmit(newValues);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      <Form id={FORM_ID}>
        <Stack spacing="3">
          <CustomTextInput
            name="name"
            label="Name"
            tooltip={DATASET.name.tooltip}
            data-testid="name-input"
            variant="block"
          />
          <CustomTextInput
            name="description"
            label="Description"
            tooltip={DATASET.description.tooltip}
            data-testid="description-input"
            variant="block"
          />
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditDatasetForm;
