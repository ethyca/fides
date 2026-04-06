import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraStack as Stack,
  Icons,
  useMessage,
} from "fidesui";
import {
  FieldArray,
  Form,
  FormikHelpers,
  useFormikContext,
} from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import {
  CustomSwitch,
  CustomTextInput,
  Label,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
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

export type SSOProviderFormValues = Omit<
  OpenIDProviderCreate,
  "provider" | "client_id" | "client_secret"
> & {
  id?: string;
  provider?: ProviderEnum;
  client_id?: string;
  client_secret?: string;
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

export const getSSOProviderFormValidationSchema = (isEditMode: boolean) =>
  Yup.object().shape({
    provider: Yup.string().required().label("Provider"),
    name: Yup.string().required().label("Name"),
    client_id: isEditMode
      ? Yup.string().optional().label("Client ID")
      : Yup.string().required().label("Client ID"),
    client_secret: isEditMode
      ? Yup.string().optional().label("Client Secret")
      : Yup.string().required().label("Client Secret"),
    // nullable — the API type allows null for scopes so that the form save button is not disabled (Array<string> | null)
    scopes: Yup.array().of(Yup.string()).nullable().label("Scopes"),
    verify_email: Yup.boolean().optional().label("Verify Email"),
    verify_email_field: Yup.string()
      .optional()
      .nullable()
      .label("Userinfo object verify email field"),
    email_field: Yup.string()
      .optional()
      .nullable()
      .label("Userinfo object email field"),
  });

/**
 * Shared mutation submission logic for both create and edit SSO provider flows.
 * Intended for use by the modal wrappers (AddSSOProviderModal, EditSSOProviderModal).
 */
export const useSSOProviderSubmit = ({
  openIDProvider,
  onClose,
  onSuccess,
}: {
  openIDProvider?: OpenIDProvider;
  onClose: () => void;
  onSuccess?: (provider: OpenIDProvider) => void;
}) => {
  const isEditMode = !!openIDProvider;
  const message = useMessage();
  const [createOpenIDProviderMutationTrigger] =
    useCreateOpenIDProviderMutation();
  const [updateOpenIDProviderMutation] = useUpdateOpenIDProviderMutation();

  const handleResult = (
    result:
      | { data: OpenIDProvider }
      | { error: FetchBaseQueryError | SerializedError },
    formikHelpers: FormikHelpers<SSOProviderFormValues>,
  ) => {
    if (isErrorResult(result)) {
      message.error(
        getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the SSO provider. Please try again.",
        ),
      );
    } else {
      message.success("SSO provider configuration saved.");
      onClose();
      formikHelpers.resetForm({});
      onSuccess?.(result.data);
    }
  };

  const handleSubmit = async (
    values: SSOProviderFormValues,
    formikHelpers: FormikHelpers<SSOProviderFormValues>,
  ) => {
    if (isEditMode) {
      // Strip empty credential fields — the backend preserves existing encrypted
      // values when client_id / client_secret are absent from the payload.
      const {
        client_id: clientId,
        client_secret: clientSecret,
        ...rest
      } = values;
      const payload = {
        ...rest,
        ...(clientId ? { client_id: clientId } : {}),
        ...(clientSecret ? { client_secret: clientSecret } : {}),
      };
      const result = await updateOpenIDProviderMutation(payload);
      handleResult(result, formikHelpers);
    } else {
      const result = await createOpenIDProviderMutationTrigger(values);
      handleResult(result, formikHelpers);
    }
  };

  return { handleSubmit };
};

const CustomProviderExtraFields = () => {
  const {
    values: { verify_email: verifyEmail, scopes = [] },
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
        tooltip="Require user emails to be verified, defaults to true"
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
      <FieldArray
        name="scopes"
        render={(arrayHelpers) => (
          <Flex flexDir="column">
            <Label size="small">Scopes</Label>
            {scopes?.map((_: string, index: number) => (
              // eslint-disable-next-line react/no-array-index-key
              <Flex flexDir="row" key={index} my="3">
                <CustomTextInput
                  name={`scopes[${index}]`}
                  variant="stacked"
                  placeholder="openid"
                />
                <Button
                  aria-label="delete-scope"
                  icon={<Icons.TrashCan />}
                  className="z-[2] ml-4"
                  onClick={() => {
                    arrayHelpers.remove(index);
                  }}
                />
              </Flex>
            ))}
            <Flex justifyContent="center">
              <Button
                aria-label="add-scope"
                className="w-full"
                onClick={() => {
                  arrayHelpers.push("");
                }}
              >
                Add scope
              </Button>
            </Flex>
          </Flex>
        )}
      />
    </>
  );
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

interface SSOProviderFormProps {
  onClose: () => void;
  isEditMode?: boolean;
}

/**
 * Pure form fields component. Requires a FormikProvider ancestor —
 * see AddSSOProviderModal / EditSSOProviderModal which supply it.
 */
const SSOProviderForm = ({ onClose, isEditMode = false }: SSOProviderFormProps) => {
  const { dirty, isValid, values } = useFormikContext<SSOProviderFormValues>();

  return (
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
          disabled={isEditMode}
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
          isRequired={!isEditMode}
          placeholder={isEditMode ? "Leave blank to keep existing" : undefined}
        />
        <CustomTextInput
          id="client_secret"
          name="client_secret"
          label="Client secret"
          type="password"
          tooltip="Client secret for your provider"
          variant="stacked"
          isRequired={!isEditMode}
          placeholder={isEditMode ? "Leave blank to keep existing" : undefined}
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
  );
};

export default SSOProviderForm;
