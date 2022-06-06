import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { DATA_QUALIFIERS } from "./constants";
import { DatasetCollection, DatasetField } from "./types";

type FormValues =
  | Pick<DatasetField, "description" | "data_qualifier" | "data_categories">
  | Pick<
      DatasetCollection,
      "description" | "data_qualifier" | "data_categories"
    >;

interface Props {
  field: FormValues;
  onClose: () => void;
  onSubmit: (values: FormValues) => void;
}

const EditCollectionOrFieldForm = ({ field, onClose, onSubmit }: Props) => {
  const initialValues: FormValues = {
    description: field.description ?? "",
    data_qualifier: field.data_qualifier,
    data_categories: field.data_categories,
  };

  const handleSubmit = (values: FormValues) => {
    onSubmit(values);
    onClose();
  };

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      <Form>
        <Stack>
          <Box>
            <CustomTextInput name="description" label="Description" />
          </Box>
          <Box>
            <CustomSelect name="data_qualifier" label="Identifiability">
              {DATA_QUALIFIERS.map((qualifier) => (
                <option key={qualifier.key} value={qualifier.key}>
                  {qualifier.label}
                </option>
              ))}
            </CustomSelect>
          </Box>
          <Box>Data Categories (todo)</Box>
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button type="submit" colorScheme="primary" size="sm">
              Save
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
