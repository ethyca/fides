import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { Box, Button, Stack, useToast } from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { OpenIDProvider } from "~/types/api";

// NOTE: This form only supports *editing* Organizations right now, and
// does not support creation/deletion. Since Fides will automatically create the
// "default_organization" on startup, this works!
//
// However, note that if the provided `organization` prop is null, the form
// will still render but all fields will be disabled and it will display as
// "loading". This allows the form to render immediately while the parent
// fetches the Organization via the API
interface OpenIDProviderFormProps {
  openIDProvider?: Organization;
  onSuccess?: (openIDProvider: Organization) => void;
}

export interface OpenIDProviderFormValues extends OpenIDProvider {}

export const defaultInitialValues: OpenIDProviderFormValues = {
  provider: "",
  client_id: "",
  client_secret: "",
};

// NOTE: These transform functions are (basically) unnecessary right now, since
// the form values are an exact match to the Organization object. However, in
// future iterations some transformation is likely to be necessary, so we've
// put these transform functions in place ahead of time to make future updates
// easier to make
export const transformOrganizationToFormValues = (
  openIDProvider: OpenIDProvider
): OpenIDProviderFormValues => ({ ...openIDProvider });

export const transformFormValuesToOpenIDProvider = (
  formValues: OpenIDProviderFormValues
): OpenIDProvider => ({
  provider: formValues.provider,
  client_id: formValues.client_id,
  client_secret: formValues.client_secret,
});

const OpenIDProviderFormValidationSchema = Yup.object().shape({
  provider: Yup.string().required().label("Provider"),
  client_id: Yup.string().required().label("Client ID"),
  client_secret: Yup.string().required().label("Client Secret"),
});

export const OpenIDProviderForm = ({
  openIDProvider,
  onSuccess,
}: OpenIDProviderFormProps) => {
  const [updateOrganizationMutation, updateOrganizationMutationResult] =
    useUpdateOrganizationMutation();

  const initialValues = useMemo(
    () =>
      openIDProvider
        ? transformOrganizationToFormValues(openIDProvider)
        : defaultInitialValues,
    [openIDProvider]
  );

  const toast = useToast();

  const handleSubmit = async (
    values: OpenIDProviderFormValues,
    formikHelpers: FormikHelpers<OpenIDProviderFormValues>
  ) => {
    const openIDProviderBody = transformFormValuesToOpenIDProvider(values);

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the OpenID Provider. Please try again."
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("OpenID Provider configuration saved."));
        // TODO: is this needed? Copied from SystemInformationForm which is more complex
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
        if (onSuccess) {
          onSuccess(openIDProviderBody);
        }
      }
    };

    const result = await updateOrganizationMutation(openIDProviderBody);
    handleResult(result);
  };

  const PROVIDER_OPTIONS = [
    { label: "Google", value: "google" },
  ];

  // Show the loading state if the openIDProvider is null or being updated
  let isLoading = !openIDProvider || updateOrganizationMutationResult.isLoading;
  isLoading = false;
  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={OpenIDProviderFormValidationSchema}
    >
      {({ dirty, isValid }) => (
        <Form data-testid="openIDProvider-form">
          <Stack spacing={4}>
            <CustomSelect
                name="provider"
                label="Provider"
                options={PROVIDER_OPTIONS}
                variant="stacked"
                isRequired
              />
            <CustomTextInput
              id="client_id"
              name="client_id"
              label="Client ID"
              disabled={isLoading}
              tooltip="Client ID for your provider"
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              id="client_secret"
              name="client_secret"
              label="Client Secret"
              disabled={isLoading}
              tooltip="Client Secret for your provider"
              variant="stacked"
              isRequired
            />
            <Box textAlign="right">
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
