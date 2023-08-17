import {
  Box,
  Button,
  Collapse,
  Heading,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import {
  CustomFieldsList,
  useCustomFields,
} from "~/features/common/custom-fields";
import {
  CustomCreatableSelect,
  CustomSelect,
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  defaultInitialValues,
  FormValues,
  transformFormValuesToSystem,
  transformSystemToFormValues,
} from "~/features/system/form";
import {
  selectAllSystems,
  useCreateSystemMutation,
  useUpdateSystemMutation,
} from "~/features/system/system.slice";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
import { ResourceTypes, System, SystemResponse } from "~/types/api";

import { usePrivacyDeclarationData } from "./privacy-declarations/hooks";

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("System name"),
});

const SystemHeading = ({ system }: { system?: SystemResponse }) => {
  const isManual = !system;
  const headingName = isManual
    ? "your new system"
    : system.name ?? "this system";

  return (
    <Heading as="h3" size="lg">
      Describe {headingName}
    </Heading>
  );
};

interface Props {
  onSuccess: (system: System) => void;
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
  const customFields = useCustomFields({
    resourceType: ResourceTypes.SYSTEM,
    resourceFidesKey: passedInSystem?.fides_key,
  });

  const { ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: true,
    includeDisabled: false,
  });

  const allEnabledDatasets = dataProps.allDatasets;

  const initialValues = useMemo(
    () =>
      passedInSystem
        ? transformSystemToFormValues(
            passedInSystem,
            customFields.customFieldValues
          )
        : defaultInitialValues,
    [passedInSystem, customFields.customFieldValues]
  );

  const [createSystemMutationTrigger, createSystemMutationResult] =
    useCreateSystemMutation();
  const [updateSystemMutationTrigger, updateSystemMutationResult] =
    useUpdateSystemMutation();
  const systems = useAppSelector(selectAllSystems);
  const isEditing = useMemo(
    () =>
      Boolean(
        passedInSystem &&
          systems?.some((s) => s.fides_key === passedInSystem?.fides_key)
      ),
    [passedInSystem, systems]
  );

  const toast = useToast();

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const systemBody = transformFormValuesToSystem(values);

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const attemptedAction = isEditing ? "editing" : "creating";
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while ${attemptedAction} the system. Please try again.`
        );
        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
        onSuccess(systemBody);
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

  const isLoading =
    updateSystemMutationResult.isLoading ||
    createSystemMutationResult.isLoading ||
    customFields.isLoading;

  const datasetSelectOptions = allEnabledDatasets
    ? allEnabledDatasets.map((ds) => ({
        value: ds.fides_key,
        label: ds.name ? ds.name : ds.fides_key,
      }))
    : [];

  const legalBasisForProfilingOptions = [
    "Explicit consent",
    "Contract",
    "Authorised by law",
  ].map((opt) => ({
    value: opt,
    label: opt,
  }));

  const legalBasisForTransferOptions = [
    "Adequacy decision",
    "Standard contractual clauses",
    "Binding corporate rules",
    "Other",
  ].map((opt) => ({
    value: opt,
    label: opt,
  }));

  const responsibilityOptions = [
    "Controller",
    "Processor",
    "Sub-Processor",
  ].map((opt) => ({
    value: opt,
    label: opt,
  }));

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values, isValid }) => (
        <Form>
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
              <CustomTextInput
                id="name"
                name="name"
                isRequired
                label="Name"
                tooltip="What display name should we use for the system?"
                variant="stacked"
              />
              <CustomTextInput
                id="fides_key"
                name="fides_key"
                isRequired
                label="Unique ID"
                disabled
                variant="stacked"
              />
              <CustomTextInput
                id="description"
                name="description"
                label="Description"
                tooltip="What services does this system perform?"
                variant="stacked"
              />
              <CustomCreatableSelect
                id="tags"
                name="tags"
                label="System Tags"
                variant="stacked"
                options={
                  initialValues.tags
                    ? initialValues.tags.map((s) => ({
                        value: s,
                        label: s,
                      }))
                    : []
                }
                tooltip="Are there any tags to associate with this system?"
                isMulti
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Dataset reference">
              <CustomSelect
                name="dataset_references"
                label="Dataset references"
                options={datasetSelectOptions}
                tooltip="Is there a dataset configured for this system?"
                isMulti
                variant="stacked"
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Data processing properties">
              <Stack spacing={0}>
                <Box mb={4}>
                  <CustomSwitch
                    name="processes_personal_data"
                    label="This system processes personal data"
                    tooltip="Does this system process personal data?"
                    variant="stacked"
                  />
                </Box>
                <Box padding={4} borderRadius={4} backgroundColor="gray.50">
                  <Stack spacing={0}>
                    <CustomSwitch
                      name="exempt_from_privacy_regulations"
                      label="This system is exempt from privacy regulations"
                      tooltip="Is this system exempt from privacy regulations?"
                      disabled={!values.processes_personal_data}
                      variant="stacked"
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
                      <CustomSwitch
                        name="uses_profiling"
                        label="This system performs profiling"
                        tooltip="Does this system perform profiling that could have a legal effect?"
                        variant="stacked"
                      />
                      <Collapse
                        in={values.uses_profiling}
                        animateOpacity
                        style={{
                          overflow: "visible",
                        }}
                      >
                        <Box mt={4}>
                          <CustomSelect
                            name="legal_basis_for_profiling"
                            label="Legal basis for profiling"
                            options={legalBasisForProfilingOptions}
                            tooltip="What is the legal basis under which profiling is performed?"
                            isRequired={values.uses_profiling}
                            variant="stacked"
                          />
                        </Box>
                      </Collapse>
                    </Stack>
                    <Stack spacing={0}>
                      <CustomSwitch
                        name="does_international_transfers"
                        label="This system transfers data"
                        tooltip="Does this system transfer data to other countries or international organizations?"
                        variant="stacked"
                      />
                      <Collapse
                        in={values.does_international_transfers}
                        animateOpacity
                        style={{
                          overflow: "visible",
                        }}
                      >
                        <Box mt={4}>
                          <CustomSelect
                            name="legal_basis_for_transfers"
                            label="Legal basis for transfer"
                            options={legalBasisForTransferOptions}
                            tooltip="What is the legal basis under which the data is transferred?"
                            isRequired={values.does_international_transfers}
                            variant="stacked"
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
                      />
                      <Collapse
                        in={values.requires_data_protection_assessments}
                        animateOpacity
                      >
                        <Box mt={4}>
                          <CustomTextInput
                            label="DPIA/DPA location"
                            name="dpi_location"
                            tooltip="Where is the DPA/DPIA stored?"
                            variant="stacked"
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
              <SystemFormInputGroup heading="Administrative properties">
                <CustomTextInput
                  label="Data steward"
                  name="data_steward"
                  tooltip="Who are the stewards assigned to the system?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextInput
                  label="Privacy policy URL"
                  name="privacy_policy"
                  tooltip="Where can the privacy policy be located?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextInput
                  label="Legal name"
                  name="legal_name"
                  tooltip="What is the legal name of the business?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextArea
                  label="Legal address"
                  name="legal_address"
                  tooltip="What is the legal address for the business?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextInput
                  label="Department"
                  name="department"
                  tooltip="Which department is concerned with this system?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomSelect
                  label="Responsibility"
                  name="responsibility"
                  options={responsibilityOptions}
                  tooltip="What is the role of the business with regard to data processing?"
                  variant="stacked"
                  isMulti
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextInput
                  label="Legal contact (DPO)"
                  name="legal_contact"
                  tooltip="What is the official privacy contact information?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextInput
                  label="Joint controller"
                  name="joint_controller"
                  tooltip="Who are the party or parties that share responsibility for processing data?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
                <CustomTextArea
                  label="Data security practices"
                  name="data_security_practices"
                  tooltip="Which data security practices are employed to keep the data safe?"
                  variant="stacked"
                  disabled={
                    !values.processes_personal_data ||
                    values.exempt_from_privacy_regulations
                  }
                />
              </SystemFormInputGroup>
              {values.fides_key ? (
                <SystemFormInputGroup heading="Custom fields">
                  <CustomFieldsList
                    resourceType={ResourceTypes.SYSTEM}
                    resourceFidesKey={values.fides_key}
                  />
                </SystemFormInputGroup>
              ) : null}
            </Collapse>
          </Stack>
          <Box mt={6}>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isDisabled={isLoading || !dirty || !isValid}
              isLoading={isLoading}
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
