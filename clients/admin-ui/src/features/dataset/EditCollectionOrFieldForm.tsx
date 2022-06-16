import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { DATA_QUALIFIERS } from "./constants";
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

  // Copied from https://ethyca.github.io/fides/1.6.1/language/resources/dataset/
  const descriptionTooltip = `A human-readable description of the ${dataType}`;
  const dataQualifierTooltip =
    dataType === "collection"
      ? "Arrays of Data Qualifier resources, identified by fides_key, that apply to all fields in the collection."
      : "A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.";
  const dataCategoryTooltip =
    dataType === "collection"
      ? "Arrays of Data Qualifier resources, identified by fides_key, that apply to all fields in the collection."
      : "Arrays of Data Categories, identified by fides_key, that applies to this field.";

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
