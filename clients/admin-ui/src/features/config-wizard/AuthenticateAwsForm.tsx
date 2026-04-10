import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Select,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import {
  GenerateResponse,
  GenerateTypes,
  System,
  ValidTargets,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

import ErrorPage from "../common/errors/ErrorPage";
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

export const AuthenticateAwsForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();

  const [scannerError, setScannerError] = useState<ParsedError>();

  // Track submittable state
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  useEffect(() => {
    setIsDirty(form.isFieldsTouched());
  }, [form, allValues]);

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
    message.success(
      `Your scan was successfully completed, with ${systems.length} new systems detected!`,
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

  const onFinish = async (values: FormValues) => {
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

  const isSubmitting = isLoading;

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
          { title: "Authenticate AWS scanner" },
        ]}
      />

      {isSubmitting && (
        <ScannerLoading
          title="System scanning in progress"
          onClose={handleCancel}
        />
      )}

      {scannerError && (
        <>
          <ErrorPage
            error={scannerError}
            defaultMessage={
              scannerError.status === 403
                ? "Fides was unable to scan AWS. It appears that the credentials were valid to login but they did not have adequate permission to complete the scan."
                : "Fides was unable to scan your infrastructure. Please ensure your credentials are accurate and inspect the error log below for more details."
            }
            fullScreen={false}
            showReload={false}
          />
          {scannerError.status === 403 && (
            <Typography.Paragraph type="secondary" data-testid="permission-msg">
              To fix this issue, double check that you have granted the required
              permissions to these credentials as part of your IAM policy. If
              you need more help in configuring IAM policies, you can read about
              them in the{" "}
              <DocsLink href="https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_access-management.html">
                AWS documentation
              </DocsLink>
              .
            </Typography.Paragraph>
          )}
        </>
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={initialValues}
        data-testid="authenticate-aws-form"
      >
        <Flex vertical gap="large">
          {!isSubmitting && !scannerError && (
            <Card>
              <Flex vertical gap="small" className="w-full max-w-xl">
                <Typography.Paragraph>
                  To use the scanner to inventory systems in AWS, you must first
                  authenticate to your AWS cloud by providing the following
                  information:
                </Typography.Paragraph>
                <Form.Item
                  name="aws_access_key_id"
                  label="Access Key ID"
                  tooltip="The Access Key ID created by the cloud hosting provider."
                  rules={[
                    { required: true, message: "Access Key ID is required" },
                    {
                      pattern: /^\w+$/,
                      message: "Cannot contain spaces or special characters",
                    },
                  ]}
                >
                  <Input data-testid="input-aws_access_key_id" />
                </Form.Item>
                <Form.Item
                  name="aws_secret_access_key"
                  label="Secret"
                  tooltip="The secret associated with the Access Key ID used for authentication."
                  rules={[
                    { required: true, message: "Secret is required" },
                    {
                      pattern: /^[^\s]+$/,
                      message: "Cannot contain spaces",
                    },
                  ]}
                >
                  <Input.Password data-testid="input-aws_secret_access_key" />
                </Form.Item>
                <Form.Item
                  name="aws_session_token"
                  label="Session Token"
                  tooltip="The session token when using temporary credentials."
                  rules={[
                    {
                      pattern: /^[^\s]+$/,
                      message: "Cannot contain spaces",
                    },
                  ]}
                >
                  <Input.Password data-testid="input-aws_session_token" />
                </Form.Item>
                <Form.Item
                  name="region_name"
                  label="AWS Region"
                  tooltip="The geographic region of the cloud hosting provider you would like to scan."
                  rules={[
                    { required: true, message: "Default Region is required" },
                  ]}
                >
                  <Select
                    aria-label="AWS Region"
                    options={AWS_REGION_OPTIONS}
                    placeholder="Select a region"
                    data-testid="controlled-select-region_name"
                  />
                </Form.Item>
              </Flex>
            </Card>
          )}
          {!isSubmitting && (
            <Flex gap="small" justify="end">
              <Button onClick={handleCancel}>Cancel</Button>
              {!scannerError && (
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={!isDirty || !submittable}
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
    </Flex>
  );
};

export default AuthenticateAwsForm;
