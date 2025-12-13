import { AntButton as Button, Box, HStack, Stack, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFlags } from "~/features/common/features";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  GenerateResponse,
  GenerateTypes,
  OktaConfig,
  System,
  ValidTargets,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

import { NextBreadcrumb } from "../common/nav/NextBreadcrumb";
import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
import { isSystem } from "./helpers";
import { useGenerateMutation } from "./scanner.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

// OAuth2 config type for new authentication method
type OktaOAuth2Config = {
  orgUrl: string;
  clientId: string;
  privateKey: string;
  scopes: string[];
};

// Token-based config for legacy authentication
type OktaTokenConfig = {
  orgUrl: string;
  token: string;
};

const oauth2InitialValues = {
  orgUrl: "",
  clientId: "",
  privateKey: "",
  scopes: "okta.apps.read",
};

const tokenInitialValues = {
  orgUrl: "",
  token: "",
};

type OAuth2FormValues = typeof oauth2InitialValues;
type TokenFormValues = typeof tokenInitialValues;

const OAuth2ValidationSchema = Yup.object().shape({
  orgUrl: Yup.string().required().trim().url().label("Organization URL"),
  clientId: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Client ID"),
  privateKey: Yup.string()
    .required()
    .trim()
    .test(
      "is-valid-key",
      "Private key must be in PEM format (starts with -----BEGIN RSA PRIVATE KEY-----)",
      (value) => !value || value.includes("-----BEGIN"),
    )
    .label("Private Key"),
  scopes: Yup.string()
    .required()
    .trim()
    .label("Scopes")
    .default("okta.apps.read"),
});

const TokenValidationSchema = Yup.object().shape({
  orgUrl: Yup.string().required().trim().url().label("Organization URL"),
  token: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Token"),
});

const AuthenticateOktaForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const { successAlert } = useAlert();
  const { flags } = useFlags();

  const [scannerError, setScannerError] = useState<ParsedError>();

  const useOAuth2 = flags.alphaNewOktaAuth;

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
    successAlert(
      `Your scan was successfully completed, with ${systems.length} new systems detected!`,
      `Scan Successfully Completed`,
      { isClosable: true },
    );
  };
  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message: "Our system encountered a problem while connecting to Okta.",
    });
    setScannerError(parsedError);
  };
  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  const [generate, { isLoading }] = useGenerateMutation();

  const handleOAuth2Submit = async (values: OAuth2FormValues) => {
    setScannerError(undefined);

    const config: OktaOAuth2Config = {
      ...values,
      scopes: values.scopes ? [values.scopes] : ["okta.apps.read"],
    };

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config: config as unknown as OktaConfig,
        target: ValidTargets.OKTA,
        type: GenerateTypes.SYSTEMS,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      handleResults(result.data.generate_results);
    }
  };

  const handleTokenSubmit = async (values: TokenFormValues) => {
    setScannerError(undefined);

    const config: OktaTokenConfig = {
      orgUrl: values.orgUrl,
      token: values.token,
    };

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config: config as OktaConfig,
        target: ValidTargets.OKTA,
        type: GenerateTypes.SYSTEMS,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      handleResults(result.data.generate_results);
    }
  };

  if (useOAuth2) {
    return (
      <Formik
        initialValues={oauth2InitialValues}
        validationSchema={OAuth2ValidationSchema}
        onSubmit={handleOAuth2Submit}
      >
        {({ isValid, isSubmitting, dirty }) => (
          <Form data-testid="authenticate-okta-form">
            <Stack spacing={10}>
              {isSubmitting ? (
                <ScannerLoading
                  title="System scanning in progress"
                  onClose={handleCancel}
                />
              ) : null}

              {scannerError ? <ScannerError error={scannerError} /> : null}
              {!isSubmitting && !scannerError ? (
                <>
                  <Box>
                    <NextBreadcrumb
                      className="mb-4"
                      items={[
                        {
                          title: "Add systems",
                          href: "",
                          onClick: (e) => {
                            e.preventDefault();
                            handleCancel();
                          },
                        },
                        { title: "Authenticate Okta Scanner" },
                      ]}
                    />
                    <Text>
                      To use the scanner to inventory systems in Okta, you must
                      first authenticate using OAuth2 Client Credentials.
                      You&apos;ll need to create an API Services application in
                      Okta and generate an RSA key pair.
                    </Text>
                  </Box>
                  <Stack>
                    <CustomTextInput
                      name="orgUrl"
                      label="Organization URL"
                      tooltip="The URL for your organization's Okta account (e.g. https://your-org.okta.com)"
                      placeholder="https://your-org.okta.com"
                    />
                    <CustomTextInput
                      name="clientId"
                      label="Client ID"
                      tooltip="The OAuth2 client ID from your Okta API Services application"
                      placeholder="0oa1abc2def3ghi4jkl5"
                    />
                    <CustomTextArea
                      name="privateKey"
                      label="Private key"
                      tooltip="RSA private key in PEM or JWK format for OAuth2 authentication"
                      placeholder="-----BEGIN PRIVATE KEY-----&#10;MIIEvgIBADANBgkqhkiG9w0...&#10;-----END PRIVATE KEY-----"
                      textAreaProps={{
                        rows: 8,
                        style: { fontFamily: "monospace", fontSize: "12px" },
                      }}
                    />
                    <CustomTextInput
                      name="scopes"
                      label="Scopes"
                      tooltip="OAuth2 scopes to request. Default is okta.apps.read for application discovery"
                      placeholder="okta.apps.read"
                    />
                  </Stack>
                </>
              ) : null}
              {!isSubmitting ? (
                <HStack>
                  <Button onClick={handleCancel}>Cancel</Button>
                  <Button
                    htmlType="submit"
                    type="primary"
                    disabled={!dirty || !isValid}
                    loading={isLoading}
                    data-testid="submit-btn"
                  >
                    Save and continue
                  </Button>
                </HStack>
              ) : null}
            </Stack>
          </Form>
        )}
      </Formik>
    );
  }

  return (
    <Formik
      initialValues={tokenInitialValues}
      validationSchema={TokenValidationSchema}
      onSubmit={handleTokenSubmit}
    >
      {({ isValid, isSubmitting, dirty }) => (
        <Form data-testid="authenticate-okta-form">
          <Stack spacing={10}>
            {isSubmitting ? (
              <ScannerLoading
                title="System scanning in progress"
                onClose={handleCancel}
              />
            ) : null}

            {scannerError ? <ScannerError error={scannerError} /> : null}
            {!isSubmitting && !scannerError ? (
              <>
                <Box>
                  <NextBreadcrumb
                    className="mb-4"
                    items={[
                      {
                        title: "Add systems",
                        href: "",
                        onClick: (e) => {
                          e.preventDefault();
                          handleCancel();
                        },
                      },
                      { title: "Authenticate Okta Scanner" },
                    ]}
                  />
                  <Text>
                    To use the scanner to inventory systems in Okta, you must
                    first authenticate to your Okta account by providing the
                    following information:
                  </Text>
                </Box>
                <Stack>
                  <CustomTextInput
                    name="orgUrl"
                    label="Domain"
                    tooltip="The URL for your organization's account on Okta"
                  />
                  <CustomTextInput
                    name="token"
                    label="Okta token"
                    type="password"
                    tooltip="The token generated by Okta for your account."
                  />
                </Stack>
              </>
            ) : null}
            {!isSubmitting ? (
              <HStack>
                <Button onClick={handleCancel}>Cancel</Button>
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={!dirty || !isValid}
                  loading={isLoading}
                  data-testid="submit-btn"
                >
                  Save and continue
                </Button>
              </HStack>
            ) : null}
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default AuthenticateOktaForm;
