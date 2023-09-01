import { Button, Heading, HStack, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { CustomTextInput } from "~/features/common/form/inputs";
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
  token: "",
};

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  orgUrl: Yup.string().required().trim().url().label("URL"),
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

  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
    successAlert(
      `Your scan was successfully completed, with ${systems.length} new systems detected!`,
      `Scan Successfully Completed`,
      { isClosable: true }
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

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config: values,
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
                <Heading size="lg">Authenticate Okta Scanner</Heading>
                <h2>
                  To use the scanner to inventory systems in Okta, you must
                  first authenticate to your Okta account by providing the
                  following information:
                </h2>
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
                <Button variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isDisabled={!dirty || !isValid}
                  isLoading={isLoading}
                  data-testid="submit-btn"
                >
                  Save and Continue
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
