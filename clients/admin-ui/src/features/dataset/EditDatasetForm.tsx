import { Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/taxonomy.slice";
import { Dataset } from "~/types/api";

import { CustomTextInput } from "../common/form/inputs";
import { DATASET } from "./constants";
import DataCategoryInput from "./DataCategoryInput";

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
  const allDataCategories = useSelector(selectDataCategories);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    initialValues.data_categories ?? [],
  );

  const handleSubmit = (formValues: FormValues) => {
    // data categories need to be handled separately since they are not a typical form element
    const newValues = {
      ...formValues,
      ...{ data_categories: checkedDataCategories },
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
          />
          <CustomTextInput
            name="description"
            label="Description"
            tooltip={DATASET.description.tooltip}
            data-testid="description-input"
          />
          <DataCategoryInput
            dataCategories={allDataCategories}
            checked={checkedDataCategories}
            onChecked={setCheckedDataCategories}
            tooltip={DATASET.data_categories.tooltip}
          />
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditDatasetForm;
