import { Button, Flex, Typography } from "fidesui";
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

import ErrorPage from "../common/errors/ErrorPage";
import { ControlledSelect } from "../common/form/ControlledSelect";
import { NextBreadcrumb } from "../common/nav/NextBreadcrumb";
import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
import { AWS_REGION_OPTIONS } from "./constants";
import { isSystem } from "./helpers";
import { useGenerateMutation } from "./scanner.slice";
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
    <Flex vertical gap="large">
      <NextBreadcrumb
        items={[
          {
            title: "Add systems",
            href: "",
            onClick: (e) => {
              e.preventDefault();
              handleCancel();
            },
          },
          { title: "Authenticate AWS Scanner" },
        ]}
      />
      <Formik
        initialValues={initialValues}
        validationSchema={ValidationSchema}
        onSubmit={handleSubmit}
      >
        {({ isValid, isSubmitting, dirty }) => (
          <>
            {isSubmitting && (
              <ScannerLoading
                title="System scanning in progress"
                onClose={handleCancel}
              />
            )}

            {scannerError && (
              <ErrorPage
                error={scannerError}
                defaultMessage="Fides was unable to scan your infrastructure. Please ensure your
        credentials are accurate and inspect the error log below for more
        details."
                fullScreen={false}
                showReload={false}
              />
            )}
            <Form data-testid="authenticate-aws-form">
              <Flex vertical gap="large">
                {!isSubmitting && !scannerError && (
                  <Flex vertical gap="small" className="w-full max-w-xl">
                    <Typography.Paragraph>
                      To use the scanner to inventory systems in AWS, you must
                      first authenticate to your AWS cloud by providing the
                      following information:
                    </Typography.Paragraph>
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
                  </Flex>
                )}
                {!isSubmitting && (
                  <Flex gap="small">
                    <Button onClick={handleCancel}>Cancel</Button>
                    {!scannerError && (
                      <Button
                        htmlType="submit"
                        type="primary"
                        disabled={!dirty || !isValid}
                        loading={isLoading}
                        data-testid="submit-btn"
                      >
                        Save and continue
                      </Button>
                    )}
                  </Flex>
                )}
              </Flex>
            </Form>
          </>
        )}
      </Formik>
    </Flex>
  );
};

export default AuthenticateAwsForm;
