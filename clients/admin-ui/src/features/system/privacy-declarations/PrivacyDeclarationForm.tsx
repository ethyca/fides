/**
 * Exports various parts of the privacy declaration form for flexibility
 */

import {
  CustomFieldsList,
  CustomFieldValues,
  useCustomFields,
} from "common/custom-fields";
import {
  Box,
  BoxProps,
  GreenCheckCircleIcon,
  Heading,
  Stack,
  Text,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo, useState } from "react";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextInput } from "~/features/common/form/inputs";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import {
  DataCategory,
  Dataset,
  DataSubject,
  DataUse,
  PrivacyDeclarationResponse,
  ResourceTypes,
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

export type FormValues = Omit<PrivacyDeclarationResponse, "cookies"> & {
  customFieldValues: CustomFieldValues;
  cookies: string[];
};

const defaultInitialValues: FormValues = {
  data_categories: [],
  data_subjects: [],
  data_use: "",
  dataset_references: [],
  customFieldValues: {},
  id: "",
  cookies: [],
};

const transformFormValueToDeclaration = (values: FormValues) => {
  const { customFieldValues, ...declaration } = values;

  return {
    ...declaration,
    // Fill in an empty string for name because of https://github.com/ethyca/fideslang/issues/98
    name: values.name ?? "",
    // Transform cookies from string back to an object with default values
    cookies: declaration.cookies.map((name) => ({ name, path: "/" })),
  };
};

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
  privacyDeclarationId,
  includeCookies,
  includeCustomFields,
}: DataProps &
  Pick<Props, "onDelete"> & {
    privacyDeclarationId?: string;
    includeCookies?: boolean;
    includeCustomFields?: boolean;
  }) => {
  const datasetOptions = allDatasets
    ? allDatasets.map((d) => ({
        label: d.name ?? d.fides_key,
        value: d.fides_key,
      }))
    : [];

  return (
    <Stack spacing={4}>
      <ControlledSelect
        id="data_use"
        label="Data use"
        name="data_use"
        options={allDataUses.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
        layout="stacked"
        disabled={!!privacyDeclarationId}
      />
      <CustomTextInput
        id="name"
        label="Processing Activity"
        name="name"
        variant="stacked"
        tooltip="The personal data processing activity or activities associated with this data use."
        disabled={!!privacyDeclarationId}
      />
      <ControlledSelect
        name="data_categories"
        label="Data categories"
        options={allDataCategories.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="What type of data is your system processing? This could be various types of user or system data."
        mode="multiple"
        layout="stacked"
        disabled
      />
      <ControlledSelect
        name="data_subjects"
        label="Data subjects"
        options={allDataSubjects.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="Whose data are you processing? This could be customers, employees or any other type of user in your system."
        mode="multiple"
        layout="stacked"
        disabled
      />
      {includeCookies ? (
        <ControlledSelect
          name="cookies"
          label="Cookies"
          mode="tags"
          layout="stacked"
        />
      ) : null}
      {allDatasets ? (
        <ControlledSelect
          name="dataset_references"
          label="Dataset references"
          options={datasetOptions}
          tooltip="Referenced Dataset fides keys used by the system."
          mode="multiple"
          layout="stacked"
        />
      ) : null}
      {includeCustomFields ? (
        <CustomFieldsList
          resourceType={ResourceTypes.PRIVACY_DECLARATION}
          resourceFidesKey={privacyDeclarationId}
        />
      ) : null}
    </Stack>
  );
};

export const transformPrivacyDeclarationToFormValues = (
  privacyDeclaration?: PrivacyDeclarationResponse,
  customFieldValues?: CustomFieldValues,
): FormValues =>
  privacyDeclaration
    ? {
        ...privacyDeclaration,
        customFieldValues: customFieldValues || {},
        cookies: privacyDeclaration.cookies?.map((cookie) => cookie.name) ?? [],
      }
    : defaultInitialValues;

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
        customFieldValues,
      ),
    [passedInInitialValues, customFieldValues],
  );

  const [showSaved, setShowSaved] = useState(false);

  const title = useMemo(() => {
    const thisDataUse = allDataUses.filter(
      (du) => du.fides_key === initialValues.data_use,
    )[0];
    if (thisDataUse) {
      return initialValues.name
        ? `${thisDataUse.name} - ${initialValues.name}`
        : thisDataUse.name;
    }
    return undefined;
  }, [allDataUses, initialValues]);

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>,
  ) => {
    const { customFieldValues: formCustomFieldValues } = values;
    const declarationToSubmit = transformFormValueToDeclaration(values);

    const success = await onSubmit(declarationToSubmit, formikHelpers);
    if (success) {
      // find the matching resource based on data use and name
      const customFieldResource = success.filter(
        (pd) =>
          pd.data_use === values.data_use &&
          // name can be undefined, so avoid comparing undefined == ""
          // (which we want to be true) - they both mean the PD has no name
          (pd.name ? pd.name === values.name : true),
      );
      if (customFieldResource.length > 0) {
        await upsertCustomFields({
          customFieldValues: formCustomFieldValues,
          fides_key: customFieldResource[0].id,
        });
      }
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
    formikHelpers: FormikHelpers<FormValues>,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  onDelete: (
    declaration: PrivacyDeclarationResponse,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  initialValues?: PrivacyDeclarationResponse;
  privacyDeclarationId?: string;
  includeCustomFields?: boolean;
  includeCookies?: boolean;
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
      privacyDeclarationId: passedInInitialValues?.id,
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
          <FormGuard id="PrivacyDeclaration" name="New Privacy Declaration" />
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
