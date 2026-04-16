import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { ParsedError, parseError } from "~/features/common/helpers";
import { OKTA_AUTH_DESCRIPTION } from "~/features/integrations/integration-type-info/oktaInfo";
import {
  GenerateResponse,
  GenerateTypes,
  OktaConfig,
  System,
  ValidTargets,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors/api";

import ErrorPage from "../common/errors/ErrorPage";
import { NextBreadcrumb } from "../common/nav/NextBreadcrumb";
import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
import { isSystem } from "./helpers";
import { useGenerateMutation } from "./scanner.slice";
import ScannerLoading from "./ScannerLoading";

const initialValues = {
  orgUrl: "",
  clientId: "",
  privateKey: "",
  scopes: "okta.apps.read",
};

type FormValues = typeof initialValues;

export const AuthenticateOktaForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();

  const [scannerError, setScannerError] = useState<ParsedError>();

  // Track submittable state
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    const checkValidity = async () => {
      try {
        await form.validateFields({ validateOnly: true });
        setSubmittable(true);
      } catch {
        setSubmittable(false);
      }
    };
    checkValidity();
  }, [form, allValues]);

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
    message.success(
      `Your scan was successfully completed, with ${systems.length} new systems detected!`,
    );
  };
  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  const [generate, { isLoading }] = useGenerateMutation();

  const onFinish = async (values: FormValues) => {
    setScannerError(undefined);

    const config: OktaConfig = {
      ...values,
      scopes: values.scopes
        ? values.scopes.split(",").map((s) => s.trim())
        : ["okta.apps.read"],
    };

    try {
      const result = await generate({
        organization_key: organizationKey,
        generate: {
          config,
          target: ValidTargets.OKTA,
          type: GenerateTypes.SYSTEMS,
        },
      }).unwrap();

      handleResults(result.generate_results);
    } catch (error) {
      const parsedError = parseError(error as RTKErrorResult["error"], {
        status: 500,
        message: "Our system encountered a problem while connecting to Okta.",
      });
      setScannerError(parsedError);
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
          { title: "Authenticate Okta scanner" },
        ]}
      />

      {isLoading && (
        <ScannerLoading
          title="System scanning in progress"
          onClose={handleCancel}
        />
      )}

      {scannerError && (
        <ErrorPage
          error={scannerError}
          defaultMessage="Fides was unable to scan your infrastructure. Please ensure your credentials are accurate and inspect the error log below for more details."
          fullScreen={false}
          showReload={false}
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={initialValues}
        data-testid="authenticate-okta-form"
      >
        <Flex vertical gap="large">
          {!isLoading && !scannerError && (
            <Card>
              <Flex vertical gap="small" className="w-full max-w-xl">
                <Typography.Paragraph>
                  {OKTA_AUTH_DESCRIPTION}
                </Typography.Paragraph>
                <Form.Item
                  name="orgUrl"
                  label="Organization URL"
                  tooltip="The URL for your organization's Okta account (e.g. https://your-org.okta.com)"
                  rules={[
                    {
                      required: true,
                      message: "Organization URL is required",
                    },
                    { type: "url", message: "Must be a valid URL" },
                  ]}
                >
                  <Input
                    placeholder="https://your-org.okta.com"
                    data-testid="input-orgUrl"
                  />
                </Form.Item>
                <Form.Item
                  name="clientId"
                  label="Client ID"
                  tooltip="The OAuth2 client ID from your Okta API Services application"
                  rules={[
                    { required: true, message: "Client ID is required" },
                    {
                      pattern: /^[^\s]+$/,
                      message: "Cannot contain spaces",
                    },
                  ]}
                >
                  <Input
                    placeholder="0oa1abc2def3ghi4jkl5"
                    data-testid="input-clientId"
                  />
                </Form.Item>
                <Form.Item
                  name="privateKey"
                  label="Private key"
                  tooltip="RSA private key in JWK format for OAuth2 authentication"
                  rules={[
                    { required: true, message: "Private key is required" },
                    {
                      validator: (_, value) => {
                        if (!value) {
                          return Promise.resolve();
                        }
                        try {
                          JSON.parse(value);
                          return Promise.resolve();
                        } catch {
                          return Promise.reject(
                            new Error(
                              "Private key must be valid JSON. Paste the JWK downloaded from Okta.",
                            ),
                          );
                        }
                      },
                    },
                  ]}
                >
                  <Input.TextArea
                    rows={8}
                    className="font-mono text-xs"
                    placeholder='{"kty":"RSA","kid":"...","n":"...","e":"AQAB","d":"..."}'
                    data-testid="input-privateKey"
                  />
                </Form.Item>
                <Form.Item
                  name="scopes"
                  label="Scopes"
                  tooltip="OAuth2 scopes to request. Default is okta.apps.read for application discovery"
                  rules={[
                    { required: true, message: "Scopes is required" },
                    {
                      validator: (_, value) => {
                        if (!value) {
                          return Promise.resolve();
                        }
                        const scopes = value
                          .split(",")
                          .map((s: string) => s.trim());
                        if (
                          scopes.every(
                            (scope: string) =>
                              scope.length > 0 && !/\s/.test(scope),
                          )
                        ) {
                          return Promise.resolve();
                        }
                        return Promise.reject(
                          new Error(
                            "Scopes must be a single scope or comma-separated list (e.g., 'okta.apps.read' or 'okta.apps.read, okta.users.read')",
                          ),
                        );
                      },
                    },
                  ]}
                >
                  <Input
                    placeholder="okta.apps.read"
                    data-testid="input-scopes"
                  />
                </Form.Item>
              </Flex>
            </Card>
          )}
          {!isLoading && (
            <Flex gap="small" justify="end">
              <Button onClick={handleCancel}>Cancel</Button>
              {!scannerError && (
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={!form.isFieldsTouched() || !submittable}
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
