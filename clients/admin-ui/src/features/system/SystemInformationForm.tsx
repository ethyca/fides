import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import {
  AntButton as Button,
  Box,
  Collapse,
  Heading,
  Stack,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  CustomFieldsList,
  useCustomFields,
} from "~/features/common/custom-fields";
import { useFeatures } from "~/features/common/features/features.slice";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  isFetchBaseQueryError,
  VendorSources,
} from "~/features/common/helpers";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
  useLazyGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import {
  selectLockedForGVL,
  setLockedForGVL,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import {
  DictSuggestionNumberInput,
  DictSuggestionSwitch,
  DictSuggestionTextArea,
  DictSuggestionTextInput,
} from "~/features/system/dictionary-form/DictSuggestionInputs";
import { transformDictDataUseToDeclaration } from "~/features/system/dictionary-form/helpers";
import {
  defaultInitialValues,
  FormValues,
  transformFormValuesToSystem,
  transformSystemToFormValues,
} from "~/features/system/form";
import {
  useCreateSystemMutation,
  useGetAllSystemsQuery,
  useLazyGetSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system/system.slice";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
import VendorSelector from "~/features/system/VendorSelector";
import { ResourceTypes, SystemResponse } from "~/types/api";

import { ControlledSelect } from "../common/form/ControlledSelect";
import { usePrivacyDeclarationData } from "./privacy-declarations/hooks";
import {
  legalBasisForProfilingOptions,
  legalBasisForTransferOptions,
  responsibilityOptions,
} from "./SystemInformationFormSelectOptions";

const SystemHeading = ({ system }: { system?: SystemResponse }) => {
  const isManual = !system;
  const headingName = isManual
    ? "your new system"
    : (system.name ?? "this system");

  return (
    <Heading as="h3" size="lg">
      Describe {headingName}
    </Heading>
  );
};

interface Props {
  onSuccess: (system: SystemResponse) => void;
  system?: SystemResponse;
  withHeader?: boolean;
  children?: React.ReactNode;
}

const SystemInformationForm = ({
  onSuccess,
  system: passedInSystem,
  withHeader,
  children,
}: Props) => {
  const { data: systems = [] } = useGetAllSystemsQuery();

  const dispatch = useAppDispatch();
  const customFields = useCustomFields({
    resourceType: ResourceTypes.SYSTEM,
    resourceFidesKey: passedInSystem?.fides_key,
  });

  const { ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: true,
    includeDisabled: false,
  });

  const initialValues = useMemo(
    () =>
      passedInSystem
        ? transformSystemToFormValues(
            passedInSystem,
            customFields.customFieldValues,
          )
        : defaultInitialValues,
    [passedInSystem, customFields.customFieldValues],
  );

  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        name: Yup.string()
          .required()
          .label("System name")
          .test("is-unique", "", async (value, context) => {
            const { data } = await getSystemQueryTrigger({
              page: 1,
              size: 10,
              search: value,
            });
            const systemResults = data?.items || [];
            const similarSystemNames = systemResults.filter(
              (s) => s.name !== initialValues.name,
            );
            if (similarSystemNames.some((s) => s.name === value)) {
              return context.createError({
                message: `You already have a system called "${value}". Please specify a unique name for this system.`,
              });
            }
            return true;
          }),
        privacy_policy: Yup.string().min(1).url().nullable(),
      }),
    [getSystemQueryTrigger, initialValues.name],
  );

  const features = useFeatures();

  const [createSystemMutationTrigger, createSystemMutationResult] =
    useCreateSystemMutation();
  const [updateSystemMutationTrigger, updateSystemMutationResult] =
    useUpdateSystemMutation();
  useGetAllDictionaryEntriesQuery(undefined, {
    skip: !features.dictionaryService,
  });
  const [getDictionaryDataUseTrigger] = useLazyGetDictionaryDataUsesQuery();

  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const lockedForGVL = useAppSelector(selectLockedForGVL);

  const isEditing = useMemo(
    () =>
      Boolean(
        passedInSystem &&
          systems?.some((s) => s.fides_key === passedInSystem?.fides_key),
      ),
    [passedInSystem, systems],
  );

  const datasetSelectOptions = useMemo(
    () =>
      dataProps.allDatasets
        ? dataProps.allDatasets.map((ds) => ({
            value: ds.fides_key,
            label: ds.name ? ds.name : ds.fides_key,
          }))
        : [],
    [dataProps.allDatasets],
  );

  const toast = useToast();

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>,
  ) => {
    let dictionaryDeclarations;
    if (values.vendor_id && values.privacy_declarations.length === 0) {
      const dataUseQueryResult = await getDictionaryDataUseTrigger({
        vendor_id: values.vendor_id!,
      });
      if (dataUseQueryResult.isError) {
        const isNotFoundError =
          isFetchBaseQueryError(dataUseQueryResult.error) &&
          dataUseQueryResult.error.status === 404;
        if (!isNotFoundError) {
          const dataUseErrorMsg = getErrorMessage(
            dataUseQueryResult.error,
            `A problem occurred while fetching data uses from Fides Compass for your system.  Please try again.`,
          );
          toast({ status: "error", description: dataUseErrorMsg });
        }
      } else if (
        dataUseQueryResult.data &&
        dataUseQueryResult.data.items.length > 0
      ) {
        dictionaryDeclarations = dataUseQueryResult.data.items.map((dec) => ({
          ...transformDictDataUseToDeclaration(dec),
          name: dec.name ?? "",
        }));
      }
    }

    const valuesToSubmit = {
      ...values,
      privacy_declarations:
        dictionaryDeclarations ?? values.privacy_declarations,
    };

    const systemBody = transformFormValuesToSystem(valuesToSubmit);

    const handleResult = (
      result:
        | { data: SystemResponse }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const attemptedAction = isEditing ? "editing" : "creating";
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while ${attemptedAction} the system. Please try again.`,
        );
        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
        onSuccess(result.data);
        dispatch(setSuggestions("initial"));
      }
    };

    let result;
    if (isEditing) {
      result = await updateSystemMutationTrigger(systemBody);
    } else {
      result = await createSystemMutationTrigger(systemBody);
    }

    await customFields.upsertCustomFields(values);

    handleResult(result);
  };

  const handleVendorSelected = (newVendorId?: string | null) => {
    if (!features.dictionaryService) {
      return;
    }
    if (!newVendorId) {
      dispatch(setSuggestions("hiding"));
      dispatch(setLockedForGVL(false));
      return;
    }
    dispatch(setSuggestions("showing"));
    if (
      features.tcf &&
      extractVendorSource(newVendorId) === VendorSources.GVL
    ) {
      dispatch(setLockedForGVL(true));
    } else {
      dispatch(setLockedForGVL(false));
    }
  };

  const isLoading =
    updateSystemMutationResult.isLoading ||
    createSystemMutationResult.isLoading ||
    customFields.isLoading;

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values, isValid }) => (
        <Form>
          <FormGuard id="SystemInfoTab" name="System Info" />
          <Stack spacing={0} maxWidth={{ base: "100%", lg: "70%" }}>
            {withHeader ? <SystemHeading system={passedInSystem} /> : null}

            <Text fontSize="sm" fontWeight="medium">
              By providing a small amount of additional context for each system
              we can make reporting and understanding our tech stack much easier
              for everyone from engineering to legal teams. So let’s do this
              now.
            </Text>
            {withHeader ? <SystemHeading system={passedInSystem} /> : null}

            <SystemFormInputGroup heading="System details">
              {features.dictionaryService ? (
                <VendorSelector
                  label="System name"
                  options={dictionaryOptions}
                  onVendorSelected={handleVendorSelected}
                  isCreate={!passedInSystem}
                  lockedForGVL={lockedForGVL}
                />
              ) : (
                <CustomTextInput
                  id="name"
                  name="name"
                  label="System name"
                  tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                  variant="stacked"
                  isRequired
                />
              )}
              {passedInSystem?.fides_key && (
                <CustomTextInput
                  id="fides_key"
                  name="fides_key"
                  label="Unique ID"
                  disabled
                  variant="stacked"
                  tooltip="An auto-generated unique ID based on the system name"
                />
              )}
              <DictSuggestionTextArea
                id="description"
                name="description"
                label="Description"
                tooltip="What services does this system perform?"
                disabled={lockedForGVL}
              />
              <ControlledSelect
                mode="tags"
                id="tags"
                name="tags"
                label="System Tags"
                options={
                  initialValues.tags
                    ? initialValues.tags.map((s) => ({
                        value: s,
                        label: s,
                      }))
                    : []
                }
                layout="stacked"
                tooltip="Are there any tags to associate with this system?"
                disabled={lockedForGVL}
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
                disabled={lockedForGVL}
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Data processing properties">
              <Stack spacing={0}>
                <Box mb={4}>
                  <DictSuggestionSwitch
                    name="processes_personal_data"
                    label="This system processes personal data"
                    tooltip="Does this system process personal data?"
                    disabled={lockedForGVL}
                  />
                </Box>
                <Box padding={4} borderRadius={4} backgroundColor="gray.50">
                  <Stack spacing={0}>
                    <DictSuggestionSwitch
                      name="exempt_from_privacy_regulations"
                      label="This system is exempt from privacy regulations"
                      tooltip="Is this system exempt from privacy regulations?"
                      disabled={!values.processes_personal_data || lockedForGVL}
                    />
                    <Collapse
                      in={values.exempt_from_privacy_regulations}
                      animateOpacity
                    >
                      <Box mt={4}>
                        <CustomTextInput
                          name="reason_for_exemption"
                          label="Reason for exemption"
                          tooltip="Why is this system exempt from privacy regulation?"
                          variant="stacked"
                          isRequired={values.exempt_from_privacy_regulations}
                          disabled={lockedForGVL}
                        />
                      </Box>
                    </Collapse>
                  </Stack>
                </Box>
                <Collapse
                  in={
                    values.processes_personal_data &&
                    !values.exempt_from_privacy_regulations
                  }
                  style={{
                    overflow: "visible",
                  }}
                  animateOpacity
                >
                  <Stack spacing={4} mt={4}>
                    <Stack spacing={0}>
                      <DictSuggestionSwitch
                        name="uses_profiling"
                        label="This system performs profiling"
                        tooltip="Does this system perform profiling that could have a legal effect?"
                        disabled={lockedForGVL}
                      />
                      <Collapse
                        in={values.uses_profiling}
                        animateOpacity
                        style={{
                          overflow: "visible",
                        }}
                      >
                        <Box mt={4}>
                          <ControlledSelect
                            mode="multiple"
                            layout="stacked"
                            name="legal_basis_for_profiling"
                            label="Legal basis for profiling"
                            options={legalBasisForProfilingOptions}
                            tooltip="What is the legal basis under which profiling is performed?"
                            disabled={lockedForGVL}
                            isRequired={values.uses_profiling}
                          />
                        </Box>
                      </Collapse>
                    </Stack>
                    <Stack spacing={0}>
                      <DictSuggestionSwitch
                        name="does_international_transfers"
                        label="This system transfers data"
                        tooltip="Does this system transfer data to other countries or international organizations?"
                        disabled={lockedForGVL}
                      />
                      <Collapse
                        in={values.does_international_transfers}
                        animateOpacity
                        style={{
                          overflow: "visible",
                        }}
                      >
                        <Box mt={4}>
                          <ControlledSelect
                            mode="multiple"
                            layout="stacked"
                            name="legal_basis_for_transfers"
                            label="Legal basis for transfer"
                            options={legalBasisForTransferOptions}
                            tooltip="What is the legal basis under which the data is transferred?"
                            isRequired={values.does_international_transfers}
                            disabled={lockedForGVL}
                          />
                        </Box>
                      </Collapse>
                    </Stack>
                    <Stack spacing={0}>
                      <CustomSwitch
                        name="requires_data_protection_assessments"
                        label="This system requires Data Privacy Assessments"
                        tooltip="Does this system require (DPA/DPIA) assessments?"
                        variant="stacked"
                        isDisabled={lockedForGVL}
                      />
                      <Collapse
                        in={values.requires_data_protection_assessments}
                        animateOpacity
                      >
                        <Box mt={4}>
                          <CustomTextInput
                            label="DPIA/DPA location"
                            name="dpa_location"
                            tooltip="Where is the DPA/DPIA stored?"
                            variant="stacked"
                            disabled={lockedForGVL}
                            isRequired={
                              values.requires_data_protection_assessments
                            }
                          />
                        </Box>
                      </Collapse>
                    </Stack>
                  </Stack>
                </Collapse>
              </Stack>
            </SystemFormInputGroup>
            <Collapse
              in={
                values.processes_personal_data &&
                !values.exempt_from_privacy_regulations
              }
              animateOpacity
            >
              <SystemFormInputGroup heading="Cookie properties">
                <DictSuggestionSwitch
                  name="uses_cookies"
                  label="This system uses cookies"
                  tooltip="Does this system use cookies?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionSwitch
                  name="cookie_refresh"
                  label="This system refreshes cookies"
                  tooltip="Does this system automatically refresh cookies?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionSwitch
                  name="uses_non_cookie_access"
                  label="This system uses non-cookie trackers"
                  tooltip="Does this system use other types of trackers?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionNumberInput
                  name="cookie_max_age_seconds"
                  label="Maximum duration (seconds)"
                  tooltip="What is the maximum amount of time a cookie will live?"
                  disabled={lockedForGVL}
                />
              </SystemFormInputGroup>
              <SystemFormInputGroup heading="Administrative properties">
                <CustomTextInput
                  label="Data stewards"
                  name="data_stewards"
                  tooltip="Who are the stewards assigned to the system?"
                  variant="stacked"
                  disabled
                />
                <DictSuggestionTextInput
                  id="privacy_policy"
                  name="privacy_policy"
                  label="Privacy policy URL"
                  tooltip="Where can the privacy policy be located?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionTextInput
                  id="legal_name"
                  name="legal_name"
                  label="Legal name"
                  tooltip="What is the legal name of the business?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionTextArea
                  id="legal_address"
                  name="legal_address"
                  label="Legal address"
                  tooltip="What is the legal address for the business?"
                  disabled={lockedForGVL}
                />
                <CustomTextInput
                  label="Department"
                  name="administrating_department"
                  tooltip="Which department is concerned with this system?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations ||
                    lockedForGVL
                  }
                />
                <ControlledSelect
                  mode="multiple"
                  layout="stacked"
                  label="Responsibility"
                  name="responsibility"
                  options={responsibilityOptions}
                  tooltip="What is the role of the business with regard to data processing?"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations ||
                    lockedForGVL
                  }
                />
                <DictSuggestionTextInput
                  name="dpo"
                  id="dpo"
                  label="Legal contact (DPO)"
                  tooltip="What is the official privacy contact information?"
                  disabled={lockedForGVL}
                />
                <CustomTextInput
                  label="Joint controller"
                  name="joint_controller_info"
                  tooltip="Who are the party or parties that share responsibility for processing data?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations ||
                    lockedForGVL
                  }
                />
                <DictSuggestionTextInput
                  label="Data security practices"
                  name="data_security_practices"
                  id="data_security_practices"
                  tooltip="Which data security practices are employed to keep the data safe?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionTextInput
                  label="Legitimate interest disclosure URL"
                  name="legitimate_interest_disclosure_url"
                  id="legitimate_interest_disclosure_url"
                  disabled={lockedForGVL}
                />
                <DictSuggestionTextInput
                  label="Vendor deleted date"
                  name="vendor_deleted_date"
                  id="vendor_deleted_date"
                  tooltip="If this vendor is no longer active, it will be 'soft' deleted. When that occurs, it's deleted date will be recorded here for reporting."
                  // disable this field for editing:
                  // deleted date is populated by the GVL and should not be editable by users
                  disabled
                />
              </SystemFormInputGroup>
              {values.fides_key ? (
                <CustomFieldsList
                  resourceType={ResourceTypes.SYSTEM}
                  resourceFidesKey={values.fides_key}
                />
              ) : null}
            </Collapse>
          </Stack>
          <Box mt={6}>
            <Button
              htmlType="submit"
              type="primary"
              disabled={isLoading || !dirty || !isValid}
              loading={isLoading}
              data-testid="save-btn"
            >
              Save
            </Button>
          </Box>
          {children}
        </Form>
      )}
    </Formik>
  );
};

export default SystemInformationForm;
