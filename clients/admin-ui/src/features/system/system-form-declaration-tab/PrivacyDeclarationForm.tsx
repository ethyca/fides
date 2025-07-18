/**
 * Exports various parts of the privacy declaration form for flexibility
 */

import {
  AntButton as Button,
  Box,
  Collapse,
  Flex,
  Spacer,
  Stack,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import {
  CustomFieldsList,
  CustomFieldValues,
  useCustomFields,
} from "~/features/common/custom-fields";
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import { selectLockedForGVL } from "~/features/system/dictionary-form/dict-suggestion.slice";
import useLegalBasisOptions from "~/features/system/system-form-declaration-tab/useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "~/features/system/system-form-declaration-tab/useSpecialCategoryLegalBasisOptions";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
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
});

export type FormValues = Omit<PrivacyDeclarationResponse, "cookies"> & {
  customFieldValues: CustomFieldValues;
};

const defaultInitialValues: FormValues = {
  name: "",
  data_categories: [],
  data_use: "",
  data_subjects: [],
  egress: undefined,
  ingress: undefined,
  features: [],
  legal_basis_for_processing: undefined,
  flexible_legal_basis_for_processing: true,
  impact_assessment_location: "",
  retention_period: "",
  processes_special_category_data: false,
  special_category_legal_basis: undefined,
  data_shared_with_third_parties: false,
  third_parties: "",
  shared_categories: [],
  customFieldValues: {},
  id: "",
};

const transformFormValueToDeclaration = (values: FormValues) => {
  const declaration = {
    ...values,
    // fill in an empty string for name: https://github.com/ethyca/fideslang/issues/98
    name: values.name ?? "",
    special_category_legal_basis: values.processes_special_category_data
      ? values.special_category_legal_basis
      : undefined,
    third_parties: values.data_shared_with_third_parties
      ? values.third_parties
      : undefined,
    shared_categories: values.data_shared_with_third_parties
      ? values.shared_categories
      : undefined,
  };
  return declaration;
};

export interface DataProps {
  allDataCategories: DataCategory[];
  allDataUses: DataUse[];
  allDataSubjects: DataSubject[];
  allDatasets?: Dataset[];
  includeCustomFields?: boolean;
}

export const PrivacyDeclarationFormComponents = ({
  allDataUses,
  allDataCategories,
  allDataSubjects,
  allDatasets,
  values,
  includeCustomFields,
  privacyDeclarationId,
  lockedForGVL,
}: DataProps & {
  values: FormValues;
  privacyDeclarationId?: string;
  lockedForGVL?: boolean;
}) => {
  const isEditing = !!privacyDeclarationId;

  const { legalBasisOptions } = useLegalBasisOptions();

  const { specialCategoryLegalBasisOptions } =
    useSpecialCategoryLegalBasisOptions();
  const datasetSelectOptions = useMemo(
    () =>
      allDatasets
        ? allDatasets.map((ds) => ({
            value: ds.fides_key,
            label: ds.name ? ds.name : ds.fides_key,
          }))
        : [],
    [allDatasets],
  );

  return (
    <Stack spacing={4}>
      <SystemFormInputGroup heading="Data use declaration">
        <CustomTextInput
          id="name"
          label="Declaration name (optional)"
          name="name"
          tooltip="Would you like to append anything to the system name?"
          disabled={isEditing}
          variant="stacked"
        />
        <ControlledSelect
          id="data_use"
          label="Data use"
          name="data_use"
          options={allDataUses.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="For which business purposes is this data processed?"
          layout="stacked"
          isRequired
          disabled={isEditing}
        />
        <ControlledSelect
          name="data_categories"
          label="Data categories"
          options={allDataCategories.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="Which categories of personal data are collected for this purpose?"
          mode="multiple"
          isRequired
          disabled={lockedForGVL}
          layout="stacked"
        />
        <ControlledSelect
          name="data_subjects"
          label="Data subjects"
          options={allDataSubjects.map((data) => ({
            value: data.fides_key,
            label: data.fides_key,
          }))}
          tooltip="Who are the subjects for this personal data?"
          mode="multiple"
          layout="stacked"
        />
        {/* <ControlledSelect
          name="data_sources"
          label="Data sources"
          options={[]}
          tooltip="Where do these categories of data come from?"
          mode="multiple"
          layout="stacked"
        /> */}
        <Stack spacing={0}>
          <ControlledSelect
            name="legal_basis_for_processing"
            label="Legal basis for processing"
            options={legalBasisOptions}
            tooltip="What is the legal basis under which personal data is processed for this purpose?"
            layout="stacked"
            disabled={lockedForGVL}
          />
          <Collapse
            in={values.legal_basis_for_processing === "Legitimate interests"}
            animateOpacity
            style={{ overflow: "visible" }}
          >
            <Box mt={4}>
              <CustomTextInput
                name="impact_assessment_location"
                label="Impact assessment location"
                tooltip="Where is the legitimate interest impact assessment stored?"
                variant="stacked"
              />
            </Box>
          </Collapse>
        </Stack>
        <Box mt={5} pl={4}>
          <CustomSwitch
            name="flexible_legal_basis_for_processing"
            label="This legal basis is flexible"
            tooltip="Has the vendor declared that the legal basis may be overridden?"
            variant="stacked"
            isDisabled={lockedForGVL}
          />
        </Box>
        <CustomTextInput
          name="retention_period"
          label="Retention period (days)"
          tooltip="How long is personal data retained for this purpose?"
          variant="stacked"
          disabled={lockedForGVL}
        />
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Features">
        <ControlledSelect
          name="features"
          label="Features"
          placeholder="Describe features..."
          tooltip="What are some features of how data is processed?"
          layout="stacked"
          disabled={lockedForGVL}
          mode="tags"
        />
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Dataset reference">
        <ControlledSelect
          name="dataset_references"
          label="Dataset references"
          options={datasetSelectOptions}
          tooltip="Is there a dataset configured for this system?"
          mode="multiple"
          layout="stacked"
        />
      </SystemFormInputGroup>
      <SystemFormInputGroup heading="Special category data">
        <Stack spacing={0}>
          <CustomSwitch
            name="processes_special_category_data"
            label="This system processes special category data"
            tooltip="Is this system processing special category data as defined by GDPR Article 9?"
            variant="stacked"
          />
          <Collapse
            in={values.processes_special_category_data}
            animateOpacity
            style={{ overflow: "visible" }}
          >
            <Box mt={4}>
              <ControlledSelect
                name="special_category_legal_basis"
                label="Legal basis for processing"
                options={specialCategoryLegalBasisOptions}
                isRequired={values.processes_special_category_data}
                tooltip="What is the legal basis under which the special category data is processed?"
                layout="stacked"
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
            in={values.data_shared_with_third_parties}
            animateOpacity
            style={{ overflow: "visible" }}
          >
            <Stack mt={4} spacing={4}>
              <CustomTextInput
                name="third_parties"
                label="Third parties"
                tooltip="Which type of third parties is the data shared with?"
                variant="stacked"
              />
              <ControlledSelect
                name="shared_categories"
                label="Shared categories"
                options={allDataCategories.map((c) => ({
                  value: c.fides_key,
                  label: c.fides_key,
                }))}
                tooltip="Which categories of personal data does this system share with third parties?"
                layout="stacked"
                mode="multiple"
              />
            </Stack>
          </Collapse>
        </Stack>
      </SystemFormInputGroup>
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
): FormValues => {
  return privacyDeclaration
    ? {
        ...privacyDeclaration,
        customFieldValues: customFieldValues || {},
      }
    : defaultInitialValues;
};

/**
 * Hook to supply all data needed for the privacy declaration form
 * Purposefully excludes redux queries so that this can be used across apps
 */
export const usePrivacyDeclarationForm = ({
  onSubmit,
  initialValues: passedInInitialValues,
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
    }
  };

  return { handleSubmit, initialValues };
};

interface Props {
  onSubmit: (
    values: PrivacyDeclarationResponse,
    formikHelpers: FormikHelpers<FormValues>,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  onCancel: () => void;
  initialValues?: PrivacyDeclarationResponse;
  privacyDeclarationId?: string;
}

export const PrivacyDeclarationForm = ({
  onSubmit,
  onCancel,
  initialValues: passedInInitialValues,
  ...dataProps
}: Props & DataProps) => {
  const privacyDeclarationId = passedInInitialValues?.id;

  const { handleSubmit, initialValues } = usePrivacyDeclarationForm({
    onSubmit,
    onCancel,
    initialValues: passedInInitialValues,
    allDataUses: dataProps.allDataUses,
    privacyDeclarationId,
  });

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values }) => (
        <Form data-testid="declaration-form">
          <FormGuard id="PrivacyDeclaration" name="New Privacy Declaration" />
          <Stack spacing={4}>
            <PrivacyDeclarationFormComponents
              values={values}
              lockedForGVL={lockedForGVL}
              privacyDeclarationId={privacyDeclarationId}
              {...dataProps}
            />
            <Flex w="100%">
              <Button onClick={onCancel} data-testid="cancel-btn">
                Cancel
              </Button>
              <Spacer />
              <Button
                type="primary"
                htmlType="submit"
                disabled={!dirty}
                data-testid="save-btn"
              >
                Save
              </Button>
            </Flex>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
