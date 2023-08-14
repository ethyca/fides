/**
 * Exports various parts of the privacy declaration form for flexibility
 */

import {
  Box,
  BoxProps,
  Button,
  ButtonGroup,
  Collapse,
  Flex,
  GreenCheckCircleIcon,
  Heading,
  Spacer,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import {
  CustomFieldsList,
  CustomFieldValues,
  useCustomFields,
} from "common/custom-fields";
import { Form, Formik, FormikHelpers, useFormikContext } from "formik";
import { useMemo, useState } from "react";
import * as Yup from "yup";

import ConfirmationModal from "~/features/common/ConfirmationModal";
import {
  CustomCreatableSelect,
  CustomNumberInput,
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import {
  DataCategory,
  Dataset,
  DataSubject,
  DataUse,
  PrivacyDeclarationResponse,
  ResourceTypes,
} from "~/types/api";

import { MockDeclarationsData } from "../MockSystemData";
import { NewDeclaration } from "../newSystemMockType";
import SystemFormInputGroup from "../SystemFormInputGroup";

export const ValidationSchema = Yup.object().shape({
  data_categories: Yup.array(Yup.string())
    .min(1, "Must assign at least one data category")
    .label("Data categories"),
  data_use: Yup.string().required().label("Data use"),
  data_subjects: Yup.array(Yup.string())
    .min(1, "Must assign at least one data subject")
    .label("Data subjects"),
});

export type FormValues = Omit<PrivacyDeclarationResponse, "cookies"> & {
  // customFieldValues: CustomFieldValues;
  cookies?: string[];
};

// const defaultInitialValues: FormValues = {
//   name: "",
//   data_categories: [],
//   data_use: "",
//   data_subjects: [],
//   egress: "",
//   ingress: "",
//   features: [],
//   legal_basis_for_processing: "",
//   impact_assessment_location: "",
//   retention_period: 0,
//   processes_special_category_data: false,
//   special_category_legal_basis: "",
//   data_shared_with_third_parties: false,
//   third_parties: "",
//   shared_categories: [],
//   cookies: [],
//   id: "",
// };

const defaultInitialValues: FormValues = {
  name: "",
  data_categories: [],
  data_use: "",
  data_qualifier: "",
  data_subjects: [],
  dataset_references: [],
  egress: [],
  ingress: [],
  cookies: [],
  id: "",
};

const transformFormValueToDeclaration = (values: FormValues) => values;

export interface DataProps {
  allDataCategories: DataCategory[];
  allDataUses: DataUse[];
  allDataSubjects: DataSubject[];
  allDatasets?: Dataset[];
}

export const PrivacyDeclarationFormComponents = ({
  allDataUses,
  allDataCategories,
  allDataSubjects,
  allDatasets,
  values,
  privacyDeclarationId,
  includeCookies,
  includeCustomFields,
}: DataProps & {
  values: FormValues;
  privacyDeclarationId?: string;
  includeCookies?: boolean;
  includeCustomFields?: boolean;
}) => {
  const { dirty, isSubmitting, isValid, initialValues } =
    useFormikContext<FormValues>();
  const deleteModal = useDisclosure();

  const datasetOptions = allDatasets
    ? allDatasets.map((d) => ({
        label: d.name ?? d.fides_key,
        value: d.fides_key,
      }))
    : [];

  const testSelectOptions = [
    "Test option 1",
    "Test option 2",
    "Test option 3",
  ].map((opt) => ({
    value: opt,
    label: opt,
  }));

  const newValues = {
    processes_special_category_data: false,
    data_shared_with_third_parties: false,
  };

  return (
    <Stack spacing={4}>
      <SystemFormInputGroup heading="Data use declaration">
        <CustomTextInput
          id="name"
          label="Declaration name (optional)"
          name="name"
          tooltip="Would you like to append anything to the system name?"
          variant="stacked"
        />
        <CustomSelect
          id="data_use"
          label="Data use"
          name="data_use"
          options={allDataUses.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="For which business purposes is this data processed?"
          variant="stacked"
          isRequired
          isDisabled={!!privacyDeclarationId}
        />
        <CustomSelect
          name="data_categories"
          label="Data categories"
          options={allDataCategories.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="Which categories of personal data are collected for this purpose?"
          isMulti
          isRequired
          variant="stacked"
        />
        <CustomSelect
          name="data_subjects"
          label="Data subjects"
          options={allDataSubjects.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="Who are the subjects for this personal data?"
          isMulti
          variant="stacked"
        />
        <CustomSelect
          name="data_sources"
          label="Data sources"
          options={testSelectOptions}
          tooltip="Where do these categories of data come from?"
          isMulti
          variant="stacked"
        />
        <CustomSelect
          name="legal_basis_for_processing"
          label="Legal basis for processing"
          options={testSelectOptions}
          tooltip="What is the legal basis under which personal data is processed for this purpose?"
          variant="stacked"
        />
        <CustomNumberInput
          name="data_retention"
          label="Retention period (days)"
          tooltip="How long is personal data retained for this purpose?"
          variant="stacked"
        />
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Features">
        <CustomTextInput
          name="features"
          label="Features"
          tooltip="What are some features of how data is processed?"
          variant="stacked"
        />
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Special categories of processing">
        <Stack spacing={0}>
          <CustomSwitch
            name="processes_special_category_data"
            label="This system processes Special Category data"
            tooltip="Is this system processing special category data as defined by GDPR Article 9?"
            variant="stacked"
          />
          <Collapse
            in={newValues.processes_special_category_data}
            animateOpacity
          >
            <Box mt={4}>
              <CustomSelect
                name="legal_basis_for_special_category_processing"
                label="Legal basis for processing"
                options={testSelectOptions}
                tooltip="What is the legal basis under which the special category data is processed?"
                variant="stacked"
              />
            </Box>
          </Collapse>
        </Stack>
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Third parties">
        <Stack spacing={0}>
          <CustomSwitch
            name="data_shared_with_third_parties"
            label="This system shares data with 3rd parties for this purpose"
            tooltip="Does this system disclose, sell, or share personal data collected for this business use with 3rd parties?"
            variant="stacked"
          />
          <Collapse
            in={newValues.data_shared_with_third_parties}
            animateOpacity
          >
            <Stack mt={4} spacing={4}>
              <CustomTextInput
                name="third_parties"
                label="Third parties"
                tooltip="Which type of third parties is the data shared with?"
                variant="stacked"
              />
              <CustomSelect
                name="shared_categories"
                label="Shared categories"
                options={testSelectOptions}
                tooltip="Which categories of personal data does this system share with third parties?"
                variant="stacked"
              />
            </Stack>
          </Collapse>
        </Stack>
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Cookies">
        <CustomSelect
          name="cookies"
          label="Cookies"
          options={testSelectOptions}
          tooltip="Which cookies are placed on consumer domains for this purpose?"
          variant="stacked"
        />
      </SystemFormInputGroup>
    </Stack>
  );
};

export const transformPrivacyDeclarationToFormValues = (
  privacyDeclaration?: PrivacyDeclarationResponse,
  customFieldValues?: CustomFieldValues
): FormValues => defaultInitialValues;
// privacyDeclaration
//   ? {
//       ...privacyDeclaration,
//       // customFieldValues: customFieldValues || {},
//       // cookies: privacyDeclaration.cookies?.map((cookie) => cookie.name) ?? [],
//     }
//   : defaultInitialValues;

/**
 * Hook to supply all data needed for the privacy declaration form
 * Purposefully excludes redux queries so that this can be used across apps
 */
export const usePrivacyDeclarationForm = ({
  onSubmit,
  initialValues: passedInInitialValues,
  allDataUses,
  privacyDeclarationId,
}: Omit<Props, "onDelete"> & Pick<DataProps, "allDataUses">) => {
  const { customFieldValues, upsertCustomFields } = useCustomFields({
    resourceType: ResourceTypes.PRIVACY_DECLARATION,
    resourceFidesKey: privacyDeclarationId,
  });

  const initialValues = useMemo(
    () =>
      transformPrivacyDeclarationToFormValues(
        passedInInitialValues,
        customFieldValues
      ),
    [passedInInitialValues, customFieldValues]
  );

  const [showSaved, setShowSaved] = useState(false);

  const title = useMemo(() => {
    const thisDataUse = allDataUses.filter(
      (du) => du.fides_key === initialValues.data_use
    )[0];
    if (thisDataUse) {
      return initialValues.name
        ? `${thisDataUse.name} - ${initialValues.name}`
        : thisDataUse.name;
    }
    return undefined;
  }, [allDataUses, initialValues]);

  const handleSubmit = (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    // onSubmit();
    console.log(values);
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
    <Box
      display="flex"
      alignItems="center"
      justifyContent="space-between"
      {...boxProps}
    >
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
    values: PrivacyDeclarationResponse,
    formikHelpers: FormikHelpers<FormValues>
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  onCancel: () => void;
  initialValues?: PrivacyDeclarationResponse;
  privacyDeclarationId?: string;
  includeCustomFields?: boolean;
  includeCookies?: boolean;
}

export const PrivacyDeclarationForm = ({
  onSubmit,
  onCancel,
  initialValues: passedInInitialValues,
  ...dataProps
}: Props & DataProps) => {
  const { handleSubmit, renderHeader, initialValues } =
    usePrivacyDeclarationForm({
      onSubmit,
      onCancel,
      initialValues: passedInInitialValues,
      allDataUses: dataProps.allDataUses,
      privacyDeclarationId: passedInInitialValues?.id,
    });

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values }) => (
        <Form>
          <FormGuard id="PrivacyDeclaration" name="New Privacy Declaration" />
          <Stack spacing={4}>
            <PrivacyDeclarationFormComponents values={values} {...dataProps} />
            <Flex w="100%">
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Spacer />
              <Button
                colorScheme="primary"
                size="sm"
                type="submit"
                data-testid="submit-btn"
              >
                Save (nothing yet)
              </Button>
            </Flex>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
