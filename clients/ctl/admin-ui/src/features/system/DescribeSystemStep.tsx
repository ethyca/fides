import { Box, Button, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import React, { useState } from "react";
import * as Yup from "yup";

import {
  CustomCreatableMultiSelect,
  CustomMultiSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import DescribeSystemsFormExtension from "~/features/system/DescribeSystemsFormExtension";
import {
  defaultInitialValues,
  FormValues,
  transformFormValuesToSystem,
} from "~/features/system/form";
import {
  useCreateSystemMutation,
  useGetAllSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system/system.slice";
import { System } from "~/types/api";

const ValidationSchema = Yup.object().shape({
  fides_key: Yup.string().required().label("System key"),
  system_type: Yup.string().required().label("System type"),
});

interface Props {
  onCancel: () => void;
  onSuccess: (system: System) => void;
  abridged?: boolean;
  initialValues?: FormValues;
}

const DescribeSystemStep = ({
  onCancel,
  onSuccess,
  abridged,
  initialValues: passedInInitialValues,
}: Props) => {
  const isEditing = !!passedInInitialValues;
  const initialValues = passedInInitialValues ?? defaultInitialValues;
  const [createSystem] = useCreateSystemMutation();
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
  const { data: systems } = useGetAllSystemsQuery();
  const systemOptions = systems
    ? systems.map((s) => ({ label: s.name ?? s.fides_key, value: s.fides_key }))
    : [];

  const toast = useToast();

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

    setIsLoading(true);

    let result;
    if (isEditing) {
      result = await updateSystem(systemBody);
    } else {
      result = await createSystem(systemBody);
    }
    handleResult(result);

    setIsLoading(false);
  };

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
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Describe your system
            </Heading>
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
                // TODO FUTURE: This tooltip text is misleading since at the moment for MVP we are manually creating a fides key for this resource
                tooltip="System keys are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
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
              <CustomCreatableMultiSelect
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
              />
              <CustomMultiSelect
                label="System dependencies"
                name="system_dependencies"
                tooltip="A list of fides keys to model dependencies."
                options={systemOptions}
              />
              {!abridged ? (
                <DescribeSystemsFormExtension values={values} />
              ) : null}
            </Stack>
            <Box>
              <Button
                onClick={() => onCancel()}
                mr={2}
                size="sm"
                variant="outline"
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                // if isEditing, always allow going to the next step
                disabled={isEditing ? false : !dirty}
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
