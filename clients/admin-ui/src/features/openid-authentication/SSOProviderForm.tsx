import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  Button,
  ChakraBox as Box,
  ChakraStack as Stack,
  useChakraToast as useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers, useFormikContext } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
} from "~/features/openid-authentication/openprovider.slice";
import {
  OpenIDProvider,
  OpenIDProviderCreate,
  ProviderEnum,
} from "~/types/api";

import { ControlledSelect } from "../common/form/ControlledSelect";

interface SSOProviderFormProps {
  openIDProvider?: OpenIDProvider;
  onSuccess?: (openIDProvider: OpenIDProvider) => void;
  onClose: () => void;
}

export type SSOProviderFormValues = Omit<
  OpenIDProviderCreate,
  "provider" | "client_id" | "client_secret"
> & {
  id?: string;
  provider?: ProviderEnum;
  client_id?: string;
  client_secret?: string;
  verify_email?: boolean;
  scopes?: string[];
};

export const defaultInitialValues: SSOProviderFormValues = {
  identifier: "",
  name: "",
  client_id: "",
  client_secret: "",
  verify_email: true,
};

export const transformOrganizationToFormValues = (
  openIDProvider: OpenIDProvider,
): SSOProviderFormValues => ({ ...openIDProvider });

const SSOProviderFormValidationSchema = Yup.object().shape({
  provider: Yup.string().required().label("Provider"),
  name: Yup.string().required().label("Name"),
  client_id: Yup.string().required().label("Client ID"),
  client_secret: Yup.string().required().label("Client Secret"),
  scopes: Yup.array().of(Yup.string()).label("Scopes"),
});

const CustomProviderExtraFields = () => {
  const {
    values: { verify_email: verifyEmail },
  } = useFormikContext<SSOProviderFormValues>();

  return (
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
      <ControlledSelect
        id="scopes"
        name="scopes"
        label="Scopes"
        tooltip="Scopes requested during authorization callback, defaults to 'openid email'"
        placeholder="openid email"
        mode="tags"
      />
      <CustomTextInput
        id="email_field"
        name="email_field"
        label="User Info Email Field"
        tooltip="Field to extract email from the user info object, defaults to 'email'"
        variant="stacked"
        placeholder="email"
      />
      <CustomSwitch
        id="verify_email"
        name="verify_email"
        label="Require Verified Email"
        tooltip="Require user emails to be verified"
        variant="stacked"
      />
      {verifyEmail && (
        <CustomTextInput
          id="verify_email_field"
          name="verify_email_field"
          label="User Info Verify Email Field"
          tooltip="Field to extract verified email flag from the user info object, defaults to 'verified_email'"
          variant="stacked"
          placeholder="verified_email"
        />
      )}
    </>
  );
};

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
        | { data: OpenIDProvider }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the SSO provider. Please try again.",
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("SSO provider configuration saved."));
        onClose();
        formikHelpers.resetForm({});
        if (onSuccess) {
          onSuccess(result.data);
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
    { label: "Azure", value: "azure" },
    { label: "Google", value: "google" },
    { label: "Okta", value: "okta" },
    { label: "Custom", value: "custom" },
  ];

  const renderAzureProviderExtraFields = () => (
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
    </>
  );

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
            <ControlledSelect
              name="provider"
              label="Provider"
              options={PROVIDER_OPTIONS}
              layout="stacked"
              isRequired
            />
            <CustomTextInput
              id="identifier"
              name="identifier"
              label="Identifier"
              tooltip="Unique identifier for your provider"
              variant="stacked"
              isRequired
              disabled={!!initialValues.id}
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
            {values.provider === "azure" && renderAzureProviderExtraFields()}
            {values.provider === "okta" && renderOktaProviderExtraFields()}
            {values.provider === "custom" && <CustomProviderExtraFields />}
            <Box textAlign="right">
              <Button
                htmlType="button"
                data-testid="cancel-btn"
                className="mr-3"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={!dirty || !isValid}
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
