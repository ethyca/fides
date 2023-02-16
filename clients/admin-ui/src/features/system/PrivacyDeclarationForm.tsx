/**
 * This file exports both a connected and unconnected version of the same component
 * to allow for more re-use
 */

import { Button, ButtonGroup, Stack } from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { CustomSelect } from "~/features/common/form/inputs";
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
import {
  DataCategory,
  DataSubject,
  DataUse,
  PrivacyDeclaration,
} from "~/types/api";

const ValidationSchema = Yup.object().shape({
  data_categories: Yup.array(Yup.string())
    .min(1, "Must assign at least one data category")
    .label("Data categories"),
  data_use: Yup.string().required().label("Data use"),
  data_subjects: Yup.array(Yup.string())
    .min(1, "Must assign at least one data subject")
    .label("Data subjects"),
});

const defaultInitialValues: PrivacyDeclaration = {
  data_categories: [],
  data_subjects: [],
  data_use: "",
};

type FormValues = typeof defaultInitialValues;

export const PrivacyDeclarationForm = ({
  onSubmit,
  initialValues: passedInInitialValues,
  allDataCategories,
  allDataUses,
  allDataSubjects,
}: Props & {
  allDataCategories: DataCategory[];
  allDataUses: DataUse[];
  allDataSubjects: DataSubject[];
}) => {
  const initialValues = passedInInitialValues ?? defaultInitialValues;

  const handleSubmit = (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    onSubmit(values, formikHelpers);
    // Reset state such that isDirty will be checked again before next save
    formikHelpers.resetForm({ values });
  };

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form data-testid="privacy-declaration-form">
          <Stack spacing={4}>
            <CustomSelect
              id="data_use"
              label="Data use"
              name="data_use"
              options={allDataUses.map((data) => ({
                value: data.fides_key,
                label: data.fides_key,
              }))}
              tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
              variant="stacked"
              singleValueBlock
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
              variant="stacked"
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
              variant="stacked"
            />
            <ButtonGroup
              size="sm"
              display="flex"
              justifyContent="space-between"
            >
              <Button variant="outline">Delete</Button>
              <Button
                type="submit"
                colorScheme="primary"
                disabled={!dirty}
                data-testid="add-btn"
              >
                Save
              </Button>
            </ButtonGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

interface Props {
  onSubmit: (
    values: PrivacyDeclaration,
    formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => void;
  initialValues?: PrivacyDeclaration;
}
const ConnectedPrivacyDeclarationForm = (props: Props) => {
  // Query subscriptions:
  useGetAllDataCategoriesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);

  return (
    <PrivacyDeclarationForm
      {...props}
      allDataCategories={allDataCategories}
      allDataSubjects={allDataSubjects}
      allDataUses={allDataUses}
    />
  );
};

export default ConnectedPrivacyDeclarationForm;
