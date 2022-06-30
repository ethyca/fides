import { Box, Button, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { COUNTRY_OPTIONS } from "~/features/common/countries";
import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";

import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { DATA_QUALIFIERS, DATASET } from "./constants";
import DataCategoryInput from "./DataCategoryInput";
import { Dataset } from "./types";

const DATA_QUALIFIERS_OPTIONS = DATA_QUALIFIERS.map((qualifier) => ({
  label: qualifier.label,
  value: qualifier.key,
}));

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
              tooltip={DATASET.name.tooltip}
              data-testid="name-input"
            />
            <CustomTextInput
              name="description"
              label="Description"
              tooltip={DATASET.description.tooltip}
              data-testid="description-input"
            />
            <CustomTextInput
              name="retention"
              label="Retention period"
              tooltip={DATASET.retention.tooltip}
              data-testid="retention-input"
            />
            <CustomSelect
              name="data_qualifier"
              label="Identifiability"
              options={DATA_QUALIFIERS_OPTIONS}
              tooltip={DATASET.data_qualifiers.tooltip}
              data-testid="identifiability-input"
            />
            <CustomMultiSelect
              name="third_country_transfers"
              label="Geographic location"
              tooltip={DATASET.third_country_transfers.tooltip}
              isSearchable
              options={COUNTRY_OPTIONS}
              data-testid="geography-input"
            />
            <DataCategoryInput
              dataCategories={allDataCategories}
              checked={checkedDataCategories}
              onChecked={setCheckedDataCategories}
              tooltip={DATASET.data_categories.tooltip}
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
