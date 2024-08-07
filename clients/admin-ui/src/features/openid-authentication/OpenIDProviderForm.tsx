import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  Box,
  Button,
  Stack,
  useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
} from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api";

interface OpenIDProviderFormProps {
  openIDProvider?: OpenIDProvider;
  onSuccess?: (openIDProvider: OpenIDProvider) => void;
  onClose: () => void;
}

export interface OpenIDProviderFormValues extends OpenIDProvider {}

export const defaultInitialValues: OpenIDProviderFormValues = {
  id: "",
  provider: "",
  client_id: "",
  client_secret: "",
};

export const transformOrganizationToFormValues = (
  openIDProvider: OpenIDProvider
): OpenIDProviderFormValues => ({ ...openIDProvider });

const OpenIDProviderFormValidationSchema = Yup.object().shape({
  provider: Yup.string().required().label("Provider"),
  client_id: Yup.string().required().label("Client ID"),
  client_secret: Yup.string().required().label("Client Secret"),
});

export const OpenIDProviderForm = ({
  openIDProvider,
  onSuccess,
  onClose,
}: OpenIDProviderFormProps) => {
  const [createOpenIDProviderMutationTrigger] =
    useCreateOpenIDProviderMutation();
  const [updateOpenIDProviderMutation] = useUpdateOpenIDProviderMutation();

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
        formikHelpers.resetForm({});
        if (onSuccess) {
          onSuccess(values);
        }
      }
    };
    if (initialValues.id) {
      const result = await updateOpenIDProviderMutation(values);
      handleResult(result);
      onClose();
    } else {
      const result = await createOpenIDProviderMutationTrigger(values);
      handleResult(result);
      onClose();
    }
  };

  const PROVIDER_OPTIONS = [{ label: "Google", value: "google" }];

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
              type="password"
              tooltip="Client ID for your provider"
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              id="client_secret"
              name="client_secret"
              label="Client Secret"
              type="password"
              tooltip="Client Secret for your provider"
              variant="stacked"
              isRequired
            />
            <Box textAlign="right">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isDisabled={!dirty || !isValid}
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
