import { AntButton as Button, Heading, HStack, Stack } from "fidesui";
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

import { ControlledSelect } from "../common/form/ControlledSelect";
import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
import { AWS_REGION_OPTIONS } from "./constants";
import { isSystem } from "./helpers";
import { useGenerateMutation } from "./scanner.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

const initialValues = {
  aws_access_key_id: "",
  aws_secret_access_key: "",
  aws_session_token: "",
  region_name: "",
};

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  aws_access_key_id: Yup.string()
    .required()
    .trim()
    .matches(/^\w+$/, "Cannot contain spaces or special characters")
    .label("Access Key ID"),
  aws_secret_access_key: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Secret"),
  aws_session_token: Yup.string()
    .optional()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Session Token (for temporary credentials)"),
  region_name: Yup.string().required().label("Default Region"),
});

const AuthenticateAwsForm = () => {
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
      message: "Our system encountered a problem while connecting to AWS.",
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
        target: ValidTargets.AWS,
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
        <Form data-testid="authenticate-aws-form">
          <Stack spacing={10}>
            {isSubmitting ? (
              <ScannerLoading
                title="System scanning in progress"
                onClose={handleCancel}
              />
            ) : null}

            {scannerError ? (
              <ScannerError error={scannerError} scanType="aws" />
            ) : null}
            {!isSubmitting && !scannerError ? (
              <>
                <Heading size="lg">Authenticate AWS Scanner</Heading>
                <h2>
                  To use the scanner to inventory systems in AWS, you must first
                  authenticate to your AWS cloud by providing the following
                  information:
                </h2>
                <Stack>
                  <CustomTextInput
                    name="aws_access_key_id"
                    label="Access Key ID"
                    tooltip="The Access Key ID created by the cloud hosting provider."
                    isRequired
                  />
                  <CustomTextInput
                    type="password"
                    name="aws_secret_access_key"
                    label="Secret"
                    tooltip="The secret associated with the Access Key ID used for authentication."
                    isRequired
                  />
                  <CustomTextInput
                    type="password"
                    name="aws_session_token"
                    label="Session Token"
                    tooltip="The session token when using temporary credentials."
                  />
                  <ControlledSelect
                    name="region_name"
                    label="AWS Region"
                    tooltip="The geographic region of the cloud hosting provider you would like to scan."
                    options={AWS_REGION_OPTIONS}
                    isRequired
                    placeholder="Select a region"
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

export default AuthenticateAwsForm;
