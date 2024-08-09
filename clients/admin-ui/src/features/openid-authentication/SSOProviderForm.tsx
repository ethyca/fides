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
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
} from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api";

interface SSOProviderFormProps {
  openIDProvider?: OpenIDProvider;
  onSuccess?: (openIDProvider: OpenIDProvider) => void;
  onClose: () => void;
}

export interface SSOProviderFormValues extends OpenIDProvider {}

export const defaultInitialValues: SSOProviderFormValues = {
  id: "",
  identifier: "",
  name: "",
  provider: "",
  client_id: "",
  client_secret: "",
};

export const transformOrganizationToFormValues = (
  openIDProvider: OpenIDProvider,
): SSOProviderFormValues => ({ ...openIDProvider });

const SSOProviderFormValidationSchema = Yup.object().shape({
  provider: Yup.string().required().label("Provider"),
  name: Yup.string().required().label("Name"),
  client_id: Yup.string().required().label("Client ID"),
  client_secret: Yup.string().required().label("Client Secret"),
});

const SSOProviderForm = ({
  openIDProvider,
  onSuccess,
  onClose,
}: SSOProviderFormProps) => {
  const [createOpenIDProviderMutationTrigger] =
    useCreateOpenIDProviderMutation();
  const [updateOpenIDProviderMutation] = useUpdateOpenIDProviderMutation();

  const initialValues = useMemo(
    () =>
      openIDProvider
        ? transformOrganizationToFormValues(openIDProvider)
        : defaultInitialValues,
    [openIDProvider],
  );

  const toast = useToast();

  const handleSubmit = async (
    values: SSOProviderFormValues,
    formikHelpers: FormikHelpers<SSOProviderFormValues>,
  ) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the OpenID Provider. Please try again.",
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("OpenID Provider configuration saved."));
        onClose();
        formikHelpers.resetForm({});
        if (onSuccess) {
          onSuccess(values);
        }
      }
    };
    if (initialValues.id) {
      const result = await updateOpenIDProviderMutation(values);
      handleResult(result);
    } else {
      const result = await createOpenIDProviderMutationTrigger(values);
      handleResult(result);
    }
  };

  const PROVIDER_OPTIONS = [
    { label: "Google", value: "google" },
    { label: "Okta", value: "okta" },
    { label: "Custom", value: "custom" },
  ];

  const renderOktaProviderExtraFields = () => (
    <CustomTextInput
      id="domain"
      name="domain"
      label="Domain"
      tooltip="Domain for your Okta provider"
      variant="stacked"
      isRequired
    />
  );

  const renderCustomProviderExtraFields = () => (
    <>
      <CustomTextInput
        id="authorization_url"
        name="authorization_url"
        label="Authorization URL"
        tooltip="Authorization URL for your provider"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        id="token_url"
        name="token_url"
        label="Token URL"
        tooltip="Token URL for your provider"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        id="userinfo_url"
        name="user_info_url"
        label="User Info URL"
        tooltip="User Info URL for your provider"
        variant="stacked"
        isRequired
      />
    </>
  );

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={SSOProviderFormValidationSchema}
    >
      {({ dirty, isValid, values }) => (
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
              id="identifier"
              name="identifier"
              label="Identifier"
              tooltip="Unique identifier for your provider"
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              id="name"
              name="name"
              label="Name"
              tooltip="Display name for your provider"
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
              label="Client secret"
              type="password"
              tooltip="Client secret for your provider"
              variant="stacked"
              isRequired
            />
            {values.provider === "okta" && renderOktaProviderExtraFields()}
            {values.provider === "custom" && renderCustomProviderExtraFields()}
            <Box textAlign="right">
              <Button
                type="submit"
                variant="outline"
                size="sm"
                data-testid="cancel-btn"
                marginRight="12px"
                onClick={onClose}
              >
                Cancel
              </Button>
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

export default SSOProviderForm;
