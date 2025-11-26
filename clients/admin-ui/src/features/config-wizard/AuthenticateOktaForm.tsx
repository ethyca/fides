import { AntButton as Button, Box, HStack, Stack, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
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

const initialValues = {
  orgUrl: "",
  clientId: "",
  privateKey: "",
  scopes: "okta.apps.read",
};

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
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
      "is-valid-json",
      "Private key must be in JWK (JSON) format. Download from Okta Admin Console.",
      (value) => {
        if (!value) return true;
        try {
          const parsed = JSON.parse(value);
          return typeof parsed === "object" && "d" in parsed;
        } catch {
          return false;
        }
      },
    )
    .label("Private Key"),
  scopes: Yup.string()
    .required()
    .trim()
    .label("Scopes")
    .default("okta.apps.read"),
});

const AuthenticateOktaForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const { successAlert } = useAlert();

  const [scannerError, setScannerError] = useState<ParsedError>();

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

  const handleSubmit = async (values: FormValues) => {
    setScannerError(undefined);

    // Convert scopes string to array for API
    const config = {
      ...values,
      scopes: values.scopes ? [values.scopes] : ["okta.apps.read"],
    };

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config,
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

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={ValidationSchema}
      onSubmit={handleSubmit}
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
                    first authenticate using OAuth2 Client Credentials. You'll
                    need to create an API Services application in Okta and
                    generate an RSA key pair.
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Need help setting up?{" "}
                    <a
                      href="https://ethyca.com/docs/guides/okta_privatekey_setup"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ textDecoration: "underline" }}
                    >
                      View setup guide
                    </a>
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
                    tooltip="Private key in JWK (JSON) format. Download from Okta: Applications > Your App > Sign On > Client Credentials > Edit > Generate new key"
                    placeholder='{"kty":"RSA","kid":"...","n":"...","e":"AQAB","d":"..."}'
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
};

export default AuthenticateOktaForm;
