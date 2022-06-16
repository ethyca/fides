import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import {
  DATA_QUALIFIERS,
  DATASET_DATA_CATEGORY,
  DATASET_DATA_QUALIFIER,
  DATASET_DESCRIPTION_TOOLTIP,
  DATASET_NAME_TOOLTIP,
  DATASET_RETENTION_TOOLTIP,
  DATASET_THIRD_COUNTRY_TRANSFERS_TOOLTIP,
} from "./constants";
import DataCategoryInput from "./DataCategoryInput";
import { Dataset } from "./types";

type FormValues = Partial<Dataset>;

interface Props {
  values: FormValues;
  onClose: () => void;
  onSubmit: (values: FormValues) => void;
}

const EditDatasetForm = ({ values, onClose, onSubmit }: Props) => {
  const initialValues: FormValues = {
    name: values.name ?? "",
    description: values.description ?? "",
    retention: values.retention ?? "",
    data_qualifier: values.data_qualifier,
    third_country_transfers: values.third_country_transfers,
    data_categories: values.data_categories,
  };
  const allDataCategories = useSelector(selectDataCategories);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    initialValues.data_categories ?? []
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
      <Form>
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="space-between"
          height="75vh"
        >
          <Stack spacing="3">
            <CustomTextInput
              name="name"
              label="Name"
              tooltip={DATASET_NAME_TOOLTIP}
            />
            <CustomTextInput
              name="description"
              label="Description"
              tooltip={DATASET_DESCRIPTION_TOOLTIP}
            />
            <CustomTextInput
              name="retention"
              label="Retention period"
              tooltip={DATASET_RETENTION_TOOLTIP}
            />
            <CustomSelect
              name="data_qualifier"
              label="Identifiability"
              tooltip={DATASET_DATA_QUALIFIER}
            >
              {DATA_QUALIFIERS.map((qualifier) => (
                <option key={qualifier.key} value={qualifier.key}>
                  {qualifier.label}
                </option>
              ))}
            </CustomSelect>
            <CustomSelect
              name="third_country_transfers"
              label="Geographic location"
              tooltip={DATASET_THIRD_COUNTRY_TRANSFERS_TOOLTIP}
            >
              {/* TODO: where do these fields come from? */}
            </CustomSelect>
            <DataCategoryInput
              dataCategories={allDataCategories}
              checked={checkedDataCategories}
              onChecked={setCheckedDataCategories}
              tooltip={DATASET_DATA_CATEGORY}
            />
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

export default EditDatasetForm;
