import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import {
  DATA_QUALIFIERS,
  DATASET_COLLECTION_DATA_CATEGORY_TOOLTIP,
  DATASET_COLLECTION_DATA_QUALIFIER_TOOLTIP,
  DATASET_COLLECTION_DESCRIPTION_TOOLTIP,
  DATASET_FIELD_DATA_CATEGORY_TOOLTIP,
  DATASET_FIELD_DATA_QUALIFIER_TOOLTIP,
  DATASET_FIELD_DESCRIPTION_TOOLTIP,
} from "./constants";
import DataCategoryInput from "./DataCategoryInput";
import { DatasetCollection, DatasetField } from "./types";

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
      ? DATASET_COLLECTION_DESCRIPTION_TOOLTIP
      : DATASET_FIELD_DESCRIPTION_TOOLTIP;
  const dataQualifierTooltip =
    dataType === "collection"
      ? DATASET_COLLECTION_DATA_QUALIFIER_TOOLTIP
      : DATASET_FIELD_DATA_QUALIFIER_TOOLTIP;
  const dataCategoryTooltip =
    dataType === "collection"
      ? DATASET_COLLECTION_DATA_CATEGORY_TOOLTIP
      : DATASET_FIELD_DATA_CATEGORY_TOOLTIP;

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
            <Box>
              <CustomTextInput
                name="description"
                label="Description"
                tooltip={descriptionTooltip}
              />
            </Box>
            <Box>
              <CustomSelect
                name="data_qualifier"
                label="Identifiability"
                tooltip={dataQualifierTooltip}
              >
                {DATA_QUALIFIERS.map((qualifier) => (
                  <option key={qualifier.key} value={qualifier.key}>
                    {qualifier.label}
                  </option>
                ))}
              </CustomSelect>
            </Box>
            <Box>
              <DataCategoryInput
                dataCategories={allDataCategories}
                checked={checkedDataCategories}
                onChecked={setCheckedDataCategories}
                tooltip={dataCategoryTooltip}
              />
            </Box>
          </Stack>
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button type="submit" colorScheme="primary" size="sm">
              Save
            </Button>
          </Box>
        </Box>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
