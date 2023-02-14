import {
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
import { useMemo, useState } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { CustomFieldsList } from "~/features/common/custom-fields";
import { CustomTextInput } from "~/features/common/form/inputs";
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

const ValidationSchema = Yup.object().shape({
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
}

const SystemInformationForm = ({
  onSuccess,
  abridged,
  system: passedInSystem,
  withHeader,
}: Props) => {
  const initialValues = useMemo(
    () =>
      passedInSystem
        ? transformSystemToFormValues(passedInSystem)
        : defaultInitialValues,
    [passedInSystem]
  );
  const [createSystem] = useCreateSystemMutation();
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
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
      {({ dirty, values, isValid }) => (
        <Form>
          <Stack spacing={6}>
            {withHeader ? <SystemHeading system={passedInSystem} /> : null}

            <Text fontSize="sm">
              By providing a small amount of additional context for each system
              we can make reporting and understanding our tech stack much easier
              for everyone from engineering to legal teams. So let’s do this
              now.
            </Text>
            <Heading as="h4" size="sm">
              System details
            </Heading>
            <Stack spacing={4}>
              {/* While we support both designs of extra form items existing, change the width only 
              when there are extra form items. When we move to only supporting one design, 
              the parent container should control the width */}
              <Stack
                spacing={4}
                maxWidth={!abridged ? { base: "100%", lg: "50%" } : undefined}
              >
                <CustomTextInput
                  id="name"
                  name="name"
                  label="System name"
                  tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                  variant="stacked"
                />
                <CustomTextInput
                  id="fides_key"
                  name="fides_key"
                  label="System Fides key"
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
              </Stack>
              {!abridged ? (
                <>
                  <Box py={6}>
                    <Divider />
                  </Box>
                  <SystemInformationFormExtension values={values} />
                </>
              ) : null}
              {isEditing && (
                <CustomFieldsList
                  resourceId={passedInSystem!.fides_key}
                  resourceType={ResourceTypes.SYSTEM}
                />
              )}
            </Stack>
            <Box>
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
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
export default SystemInformationForm;
