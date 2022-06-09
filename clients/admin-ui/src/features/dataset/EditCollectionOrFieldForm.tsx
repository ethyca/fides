import { Box, Button, FormLabel, SimpleGrid, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/data-categories.slice";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { DATA_QUALIFIERS } from "./constants";
import DataCategoryDropdown from "./DataCategoryDropdown";
import { DatasetCollection, DatasetField } from "./types";
import DataCategoryTag from "~/features/taxonomy/DataCategoryTag";

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
}

const EditCollectionOrFieldForm = ({ values, onClose, onSubmit }: Props) => {
  const initialValues: FormValues = {
    description: values.description ?? "",
    data_qualifier: values.data_qualifier,
    data_categories: values.data_categories,
  };
  const allDataCategories = useSelector(selectDataCategories);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    initialValues.data_categories ?? []
  );

  const sortedCheckedDataCategories = checkedDataCategories
    .slice()
    .sort((a, b) => a.localeCompare(b));

  const handleSubmit = (values: FormValues) => {
    // data categories need to be handled separately since they are not a typical form element
    const newValues = {
      ...values,
      ...{ data_categories: checkedDataCategories },
    };
    onSubmit(newValues);
  };

  const handleRemoveDataCategory = (dataCategoryName: string) => {
    setCheckedDataCategories(
      checkedDataCategories.filter((dc) => dc !== dataCategoryName)
    );
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
            <Box>
              <SimpleGrid columns={[1, 2]}>
                <FormLabel>Data Categories</FormLabel>
                <Stack>
                  <Box>
                    <DataCategoryDropdown
                      dataCategories={allDataCategories}
                      checked={checkedDataCategories}
                      onChecked={setCheckedDataCategories}
                    />
                  </Box>
                  <Stack>
                    {sortedCheckedDataCategories.map((dc) => (
                      <DataCategoryTag
                        key={dc}
                        name={dc}
                        onClose={() => {
                          handleRemoveDataCategory(dc);
                        }}
                      />
                    ))}
                  </Stack>
                </Stack>
              </SimpleGrid>
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
