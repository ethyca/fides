import { Box, Button, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  CustomFieldsList,
  useCustomFields,
} from "~/features/common/custom-fields";
import {
  CustomCreatableSelect,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { changeStep } from "~/features/config-wizard/config-wizard.slice";
import DescribeSystemsFormExtension from "~/features/system/DescribeSystemsFormExtension";
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
import { ResourceTypes, System } from "~/types/api";

const ValidationSchema = Yup.object().shape({
  fides_key: Yup.string().required().label("System key"),
  system_type: Yup.string().required().label("System type"),
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
}

const DescribeSystemStep = ({
  onSuccess,
  abridged,
  system: passedInSystem,
}: Props) => {
  const initialValues = useMemo(
    () =>
      passedInSystem
        ? transformSystemToFormValues(passedInSystem)
        : defaultInitialValues,
    [passedInSystem]
  );
  const [createSystemMutationTrigger, createSystemMutationResult] =
    useCreateSystemMutation();
  const [updateSystemMutationTrigger, updateSystemMutationResult] =
    useUpdateSystemMutation();
  const dispatch = useAppDispatch();
  const systems = useAppSelector(selectAllSystems);
  const systemOptions = systems
    ? systems.map((s) => ({ label: s.name ?? s.fides_key, value: s.fides_key }))
    : [];
  const isEditing = useMemo(
    () =>
      Boolean(
        passedInSystem &&
          systems?.some((s) => s.fides_key === passedInSystem?.fides_key)
      ),
    [passedInSystem, systems]
  );

  const toast = useToast();

  const customFields = useCustomFields({
    resourceType: ResourceTypes.SYSTEM,
    resourceFidesKey: passedInSystem?.fides_key,
  });

  const handleBack = () => {
    dispatch(changeStep(2));
  };

  const handleSubmit = async (values: FormValues) => {
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

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, values }) => (
        <Form>
          <Stack spacing={10}>
            <SystemHeading system={passedInSystem} />
            <div>
              By providing a small amount of additional context for each system
              we can make reporting and understanding our tech stack much easier
              for everyone from engineering to legal teams. So let’s do this
              now.
            </div>
            <Stack spacing={4}>
              <CustomTextInput
                id="name"
                name="name"
                label="System name"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <CustomTextInput
                id="fides_key"
                name="fides_key"
                label="System key"
                disabled={isEditing}
                tooltip="A string token of your own invention that uniquely identifies this System. It's your responsibility to ensure that the value is unique across all of your System objects. The value may only contain alphanumeric characters, underscores, and hyphens. ([A-Za-z0-9_.-])."
              />
              <CustomTextInput
                id="description"
                name="description"
                label="System description"
                tooltip="If you wish you can provide a description which better explains the purpose of this system."
              />
              <CustomTextInput
                id="system_type"
                label="System Type"
                name="system_type"
                tooltip="Describe the type of system being modeled, examples include: Service, Application, Third Party, etc"
              />
              <CustomCreatableSelect
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
                tooltip="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                disableMenu
                isMulti
              />
              <CustomSelect
                label="System dependencies"
                name="system_dependencies"
                tooltip="A list of fides keys to model dependencies."
                options={systemOptions}
                isMulti
              />
              {!abridged ? (
                <DescribeSystemsFormExtension values={values} />
              ) : null}
              {isEditing && (
                <CustomFieldsList
                  resourceFidesKey={passedInSystem?.fides_key}
                  resourceType={ResourceTypes.SYSTEM}
                />
              )}
            </Stack>
            <Box>
              <Button
                onClick={handleBack}
                mr={2}
                size="sm"
                variant="outline"
                data-testid="back-btn"
              >
                Back
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isDisabled={
                  isLoading ||
                  // If this system was created from scratch, the fields must be edited.
                  (!passedInSystem && !dirty)
                }
                isLoading={isLoading}
                data-testid="confirm-btn"
              >
                Confirm and Continue
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
export default DescribeSystemStep;
