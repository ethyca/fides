import { AddIcon, Box, Button, ButtonGroup, Stack } from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import {
  selectDataQualifiers,
  useGetAllDataQualifiersQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";
import { PrivacyDeclaration } from "~/types/api";

import PrivacyDeclarationFormExtension from "./PrivacyDeclarationFormExtension";

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Declaration name"),
  data_categories: Yup.array(Yup.string())
    .min(1, "Must assign at least one data category")
    .label("Data categories"),
  data_use: Yup.string().required().label("Data use"),
  data_subjects: Yup.array(Yup.string())
    .min(1, "Must assign at least one data subject")
    .label("Data subjects"),
});

const defaultInitialValues: PrivacyDeclaration = {
  name: "",
  data_categories: [],
  data_subjects: [],
  data_use: "",
  data_qualifier: "",
  dataset_references: [],
};

interface Props {
  onSubmit: (
    values: PrivacyDeclaration,
    formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => void;
  onCancel?: () => void;
  abridged?: boolean;
  initialValues?: PrivacyDeclaration;
}
const PrivacyDeclarationForm = ({
  onSubmit,
  onCancel,
  abridged,
  initialValues: passedInInitialValues,
}: Props) => {
  const isEditing = !!passedInInitialValues;
  const initialValues = passedInInitialValues ?? defaultInitialValues;

  // Query subscriptions:
  useGetAllDataCategoriesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataQualifiersQuery();
  useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const allDataQualifiers = useAppSelector(selectDataQualifiers);

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={onSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form data-testid="privacy-declaration-form">
          <Stack spacing={4}>
            <CustomTextInput
              name="name"
              label="Declaration name"
              tooltip="A system may have multiple privacy declarations, so each declaration should have a name to distinguish them clearly."
            />
            <CustomSelect
              name="data_categories"
              label="Data categories"
              options={allDataCategories?.map((data) => ({
                value: data.fides_key,
                label: data.fides_key,
              }))}
              tooltip="What type of data is your system processing? This could be various types of user or system data."
              isMulti
            />
            <CustomSelect
              id="data_use"
              label="Data use"
              name="data_use"
              options={allDataUses.map((data) => ({
                value: data.fides_key,
                label: data.fides_key,
              }))}
              tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
            />
            <CustomSelect
              name="data_subjects"
              label="Data subjects"
              options={allDataSubjects.map((data) => ({
                value: data.fides_key,
                label: data.fides_key,
              }))}
              tooltip="Whose data are you processing? This could be customers, employees or any other type of user in your system."
              isMulti
            />
            <CustomSelect
              id="data_qualifier"
              label="Data qualifier"
              name="data_qualifier"
              options={allDataQualifiers.map((data) => ({
                value: data.fides_key,
                label: data.fides_key,
              }))}
              tooltip="How identifiable is the user in the data in this system? For instance, is it anonymized data where the user is truly unknown/unidentifiable, or it is partially identifiable data?"
            />
            {!abridged ? <PrivacyDeclarationFormExtension /> : null}
          </Stack>
          <Box>
            {isEditing ? (
              <ButtonGroup size="sm" mt={2}>
                {onCancel && (
                  <Button
                    variant="outline"
                    data-testid="back-btn"
                    onClick={onCancel}
                  >
                    Back
                  </Button>
                )}
                <Button
                  colorScheme="primary"
                  type="submit"
                  data-testid="confirm-edit-btn"
                >
                  Confirm
                </Button>
              </ButtonGroup>
            ) : (
              <Button
                type="submit"
                colorScheme="purple"
                variant="link"
                disabled={!dirty}
                data-testid="add-btn"
              >
                Add <AddIcon boxSize={10} />
              </Button>
            )}
          </Box>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyDeclarationForm;
