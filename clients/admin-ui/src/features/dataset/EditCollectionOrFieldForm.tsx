import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";
import { DatasetCollection, DatasetField } from "~/types/api";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { COLLECTION, DATA_QUALIFIERS, FIELD } from "./constants";
import DataCategoryInput from "./DataCategoryInput";

const IDENTIFIER_OPTIONS = DATA_QUALIFIERS.map((dq) => ({
  value: dq.key,
  label: dq.label,
}));

type FormValues =
  | Pick<DatasetField, "description" | "data_qualifier" | "data_categories">
  | Pick<
      DatasetCollection,
      "description" | "data_qualifier" | "data_categories"
    >;

interface Props {
  values: FormValues;
  onClose: () => void;
  onSubmit: (values: FormValues) => void;
  // NOTE: If you're adding more checks on dataType, refactor this into two
  // components instead and remove this prop.
  dataType: "collection" | "field";
}

const EditCollectionOrFieldForm = ({
  values,
  onClose,
  onSubmit,
  dataType,
}: Props) => {
  const initialValues: FormValues = {
    description: values.description ?? "",
    data_qualifier: values.data_qualifier,
    data_categories: values.data_categories,
  };
  const allDataCategories = useSelector(selectDataCategories);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    initialValues.data_categories ?? []
  );

  const descriptionTooltip =
    dataType === "collection"
      ? COLLECTION.description.tooltip
      : FIELD.description.tooltip;
  const dataQualifierTooltip =
    dataType === "collection"
      ? COLLECTION.data_qualifiers.tooltip
      : FIELD.data_qualifier.tooltip;
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
      <Form>
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="space-between"
          height="80vh"
        >
          <Stack>
            <CustomTextInput
              name="description"
              label="Description"
              tooltip={descriptionTooltip}
              data-testid="description-input"
            />
            <CustomSelect
              name="data_qualifier"
              label="Identifiability"
              options={IDENTIFIER_OPTIONS}
              tooltip={dataQualifierTooltip}
              isSearchable={false}
              data-testid="identifiability-input"
            />
            <DataCategoryInput
              dataCategories={allDataCategories}
              checked={checkedDataCategories}
              onChecked={setCheckedDataCategories}
              tooltip={dataCategoryTooltip}
            />
          </Stack>
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              data-testid="save-btn"
            >
              Save
            </Button>
          </Box>
        </Box>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
