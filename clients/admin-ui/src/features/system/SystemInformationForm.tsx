import {
  Badge,
  Box,
  Button,
  Divider,
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
import SystemInformationFormExtension from "~/features/system/SystemInformationFormExtension";
import { ResourceTypes, System } from "~/types/api";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("System name"),
  fides_key: Yup.string().required().label("System key"),
});

const SystemHeading = ({ system }: { system?: System }) => {
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
  abridged?: boolean;
  system?: System;
  withHeader?: boolean;
  children?: React.ReactNode;
}

const SystemInformationForm = ({
  onSuccess,
  abridged,
  system: passedInSystem,
  withHeader,
  children,
}: Props) => {
  const customFields = useCustomFields({
    resourceType: ResourceTypes.SYSTEM,
    resourceFidesKey: passedInSystem?.fides_key,
  });

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

  const testSelectOptions = [
    "Test option 1",
    "Test option 2",
    "Test option 3",
  ].map((opt) => ({
    value: opt,
    label: opt,
  }));

  const allBadge = (
    <Badge
      color="pink.500"
      bg="white"
      height="18px"
      lineHeight="18px"
      textAlign="center"
      borderRadius="2px"
      mr={1}
    >
      ALL
    </Badge>
  );

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values, isValid }) => (
        <Form>
          <Stack spacing={6} maxWidth={{ base: "100%", lg: "70%" }}>
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
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                variant="stacked"
              />
              <CustomTextInput
                id="fides_key"
                name="fides_key"
                isRequired
                label="Fides key"
                disabled={isEditing}
                tooltip="A string token of your own invention that uniquely identifies this System. It's your responsibility to ensure that the value is unique across all of your System objects. The value may only contain alphanumeric characters, underscores, and hyphens. ([A-Za-z0-9_.-])."
                variant="stacked"
              />
              <CustomTextInput
                id="description"
                name="description"
                label="System description"
                tooltip="If you wish you can provide a description which better explains the purpose of this system."
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
                tooltip="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                isMulti
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Dataset reference">
              <CustomSelect
                name="dataset_references"
                label="Dataset references"
                options={testSelectOptions}
                tooltip="Referenced Dataset fides keys used by the system."
                isMulti
                variant="stacked"
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Data processing properties">
              <CustomSwitch
                name="processes_personal_data"
                label="This system processes personal data"
                onChange={() => console.log(values.processes_personal_data)}
                tooltip="Disabling this toggle indicates that the system does not store or process personal data."
                variant="stacked"
              />
              <Box padding={4} borderRadius={4} backgroundColor="gray.50">
                <CustomSwitch
                  name="exempt"
                  label="This system is exempt from privacy regulations"
                  tooltip="Enabling this toggle indicates that the system does process personal data but is exempt from privacy regulation."
                  variant="stacked"
                />
              </Box>
              <CustomSwitch
                name="uses_profiling"
                label="This system performs profiling"
                tooltip="Describes the use of data to profile a consumer in a way that has a legal effect."
                variant="stacked"
              />
              <CustomSelect
                name="legal_basis_for_profiling"
                label="Legal basis for profiling"
                options={testSelectOptions}
                tooltip="The legal basis for performing profiling that has a legal effect."
                isMulti
                variant="stacked"
              />
              <CustomSwitch
                name="internationalTransfers"
                label="This system transfers data"
                tooltip="This system transfers data to other countries or international organizations."
                variant="stacked"
              />
              <CustomSelect
                name="legal_basis_for_transfers"
                label="Legal basis for transfer"
                options={testSelectOptions}
                tooltip="The legal basis for performing profiling that has a legal effect."
                variant="stacked"
              />
              <CustomSwitch
                name="requires_assessments"
                label="This system requires Data Privacy Assessments"
                tooltip="This system requires data protection impact assessments (DPA/DPIA)."
                variant="stacked"
              />
              <CustomTextInput
                label="DPIA/DPA location"
                name="dpi_location"
                tooltip="Location where the DPAs or DPIAs can be found."
                variant="stacked"
              />
            </SystemFormInputGroup>
            <SystemFormInputGroup heading="Administrative properties">
              <CustomTextInput
                label="Data steward"
                name="data_steward"
                tooltip="Data stewards are assigned to manage systems and their info."
                variant="stacked"
              />
              <CustomTextInput
                label="Privacy policy"
                name="privacy_policy"
                tooltip="A URL that points to a publicly accessible privacy policy"
                variant="stacked"
              />
              <CustomTextInput
                label="Legal name"
                name="legal_name"
                tooltip="The legal name for the business"
                variant="stacked"
              />
              <CustomTextArea
                label="Legal address"
                name="legal_address"
                tooltip="The legal address for the business."
                variant="stacked"
              />
              <CustomTextInput
                label="Department"
                name="department"
                tooltip="The department within the organization."
                variant="stacked"
              />
              <CustomSelect
                label="Responsibility"
                name="responsibility"
                options={testSelectOptions}
                tooltip="The role of the business with regard to data processing."
                variant="stacked"
              />
              <CustomTextInput
                label="Legal contact (DPO)"
                name="legal_contact"
                tooltip="The official privacy contact address or DPO."
                variant="stacked"
              />
              <CustomTextInput
                label="Joint controller"
                name="joint_controller"
                tooltip="The party or parties that share the responsibility for processing personal data."
                variant="stacked"
              />
              <CustomTextArea
                label="Data security practices"
                name="data_security_practices"
                tooltip="A description of the data security practices employed."
                variant="stacked"
              />
            </SystemFormInputGroup>
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
