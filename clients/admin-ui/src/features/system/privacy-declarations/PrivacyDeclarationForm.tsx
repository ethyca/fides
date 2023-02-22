/**
 * Exports various parts of the privacy declaration form for flexibility
 */

import { ConfirmationModal } from "@fidesui/components";
import {
  Box,
  BoxProps,
  Button,
  ButtonGroup,
  GreenCheckCircleIcon,
  Heading,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { Form, Formik, FormikHelpers, useFormikContext } from "formik";
import { useMemo, useState } from "react";
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

export const ValidationSchema = Yup.object().shape({
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

export interface DataProps {
  allDataCategories: DataCategory[];
  allDataUses: DataUse[];
  allDataSubjects: DataSubject[];
}

export const PrivacyDeclarationFormComponents = ({
  allDataUses,
  allDataCategories,
  allDataSubjects,
  onDelete,
}: DataProps & Pick<Props, "onDelete">) => {
  const { dirty, isSubmitting, isValid, initialValues } =
    useFormikContext<FormValues>();
  const deleteModal = useDisclosure();

  const handleDelete = () => {
    onDelete(initialValues);
    deleteModal.onClose();
  };

  const deleteDisabled = initialValues.data_use === "";

  return (
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
        options={allDataCategories.map((data) => ({
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
      <ButtonGroup size="sm" display="flex" justifyContent="space-between">
        <Button
          variant="outline"
          onClick={deleteModal.onOpen}
          disabled={deleteDisabled}
        >
          Delete
        </Button>
        <Button
          type="submit"
          colorScheme="primary"
          disabled={!dirty || !isValid}
          isLoading={isSubmitting}
          data-testid="save-btn"
        >
          Save
        </Button>
      </ButtonGroup>
      <ConfirmationModal
        onConfirm={handleDelete}
        title="Delete data use"
        message="Are you sure you want to delete this data use? This action can't be undone."
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.onClose}
      />
    </Stack>
  );
};

/**
 * Set up subscriptions to all taxonomy resources
 */
export const useTaxonomyData = () => {
  // Query subscriptions:
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const { isLoading: isLoadingDataSubjects } = useGetAllDataSubjectsQuery();
  const { isLoading: isLoadingDataUses } = useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);

  const isLoading =
    isLoadingDataCategories || isLoadingDataSubjects || isLoadingDataUses;

  return { allDataCategories, allDataSubjects, allDataUses, isLoading };
};

/**
 * Hook to supply all data needed for the privacy declaration form
 * Purposefully excludes redux queries so that this can be used across apps
 */
export const usePrivacyDeclarationForm = ({
  onSubmit,
  initialValues: passedInInitialValues,
  allDataUses,
}: Omit<Props, "onDelete"> & Pick<DataProps, "allDataUses">) => {
  const initialValues = passedInInitialValues ?? defaultInitialValues;
  const [showSaved, setShowSaved] = useState(false);

  const title = useMemo(() => {
    const thisDataUse = allDataUses.filter(
      (du) => du.fides_key === initialValues.data_use
    )[0];
    if (thisDataUse) {
      return thisDataUse.name;
    }
    return undefined;
  }, [allDataUses, initialValues]);

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const success = await onSubmit(values, formikHelpers);
    if (success) {
      // Reset state such that isDirty will be checked again before next save
      formikHelpers.resetForm({ values });
      setShowSaved(true);
    }
  };

  const renderHeader = ({
    dirty,
    boxProps,
    /** Allow overriding showing the saved indicator */
    hideSaved,
  }: {
    dirty: boolean;
    hideSaved?: boolean;
    boxProps?: BoxProps;
  }) => (
    <Box display="flex" alignItems="center" {...boxProps}>
      {title ? (
        <Heading as="h4" size="xs" fontWeight="medium" mr={4}>
          {title}
        </Heading>
      ) : null}
      {!hideSaved && showSaved && !dirty && initialValues.data_use ? (
        <Text fontSize="sm" data-testid="saved-indicator">
          <GreenCheckCircleIcon /> Saved
        </Text>
      ) : null}
    </Box>
  );

  return { handleSubmit, renderHeader, initialValues };
};

interface Props {
  onSubmit: (
    values: PrivacyDeclaration,
    formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => Promise<boolean>;
  onDelete: (declaration: PrivacyDeclaration) => Promise<boolean>;
  initialValues?: PrivacyDeclaration;
}

export const PrivacyDeclarationForm = ({
  onSubmit,
  initialValues: passedInInitialValues,
  onDelete,
  ...dataProps
}: Props & DataProps) => {
  const { handleSubmit, renderHeader, initialValues } =
    usePrivacyDeclarationForm({
      onSubmit,
      initialValues: passedInInitialValues,
      allDataUses: dataProps.allDataUses,
    });

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form>
          <Stack spacing={4}>
            <Box data-testid="header">{renderHeader({ dirty })}</Box>
            <PrivacyDeclarationFormComponents
              onDelete={onDelete}
              {...dataProps}
            />
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
