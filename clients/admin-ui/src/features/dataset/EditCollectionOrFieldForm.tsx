import { Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { CustomTextInput } from "~/features/common/form/inputs";
import { selectDataCategories } from "~/features/taxonomy/taxonomy.slice";
import { DatasetCollection, DatasetField } from "~/types/api";

import { COLLECTION, FIELD } from "./constants";
import DataCategoryInput from "./DataCategoryInput";

export const FORM_ID = "edit-collection-or-field-form";

type FormValues =
  | Pick<DatasetField, "description" | "data_categories">
  | Pick<DatasetCollection, "description" | "data_categories">;

interface Props {
  values: FormValues;
  onSubmit: (values: FormValues) => void;
  // NOTE: If you're adding more checks on dataType, refactor this into two
  // components instead and remove this prop.
  dataType: "collection" | "field";
  showDataCategories?: boolean;
}

const EditCollectionOrFieldForm = ({
  values,
  onSubmit,
  dataType,
  showDataCategories = true,
}: Props) => {
  const initialValues: FormValues = {
    description: values.description ?? "",
    data_categories: values.data_categories,
  };
  const allEnabledDataCategories = useSelector(selectDataCategories).filter(
    (category) => category.active,
  );

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    initialValues.data_categories || [],
  );

  const descriptionTooltip =
    dataType === "collection"
      ? COLLECTION.description.tooltip
      : FIELD.description.tooltip;
  const dataCategoryTooltip =
    dataType === "collection"
      ? COLLECTION.data_categories.tooltip
      : FIELD.data_categories.tooltip;

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
        <Stack>
          <CustomTextInput
            name="description"
            label="Description"
            tooltip={descriptionTooltip}
            data-testid="description-input"
          />
          {showDataCategories && (
            <DataCategoryInput
              dataCategories={allEnabledDataCategories}
              checked={checkedDataCategories}
              onChecked={setCheckedDataCategories}
              tooltip={dataCategoryTooltip}
            />
          )}
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
