import { formatDistance } from "date-fns";
import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntSelect as Select,
  Box,
  GreenCheckCircleIcon,
  Heading,
  HStack,
} from "fidesui";
import { isEmpty, isEqual, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import {
  MESSAGING_PROVIDERS_EDIT_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
} from "~/features/common/nav/routes";
import AwsIcon from "~/features/messaging/icons/AwsIcon";

import { messagingProviders } from "../constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "../messaging.slice";
import { SendTestMessageModal } from "../SendTestMessageModal";
import { useVerifyConfiguration } from "../useVerifyConfiguration";

interface AwsSesMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const AwsSesMessagingForm = ({ configKey }: AwsSesMessagingFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const { verifyConfiguration, isVerifying, getVerificationData } =
    useVerifyConfiguration();

  const isEditMode = !!configKey;

  const [isTestMessageModalOpen, setIsTestMessageModalOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [authMethod, setAuthMethod] = useState<string>(
    isEditMode ? "**********" : "secret_keys",
  );
  const [form] = Form.useForm();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingConfiguration] =
    useUpdateMessagingConfigurationByKeyMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  // Fetch existing config data in edit mode
  const { data: existingConfig, refetch: refetchConfig } =
    useGetMessagingConfigurationByKeyQuery(
      { key: configKey! },
      { skip: !configKey },
    );

  // Memoized initial values to prevent unnecessary re-renders
  const initialValues = {
    email_from: existingConfig?.details?.email_from || "",
    domain: existingConfig?.details?.domain || "",
    aws_region: existingConfig?.details?.aws_region || "",
    auth_method: isEditMode ? "**********" : "secret_keys",
    aws_access_key_id: isEditMode ? "**********" : "",
    aws_secret_access_key: isEditMode ? "**********" : "",
    aws_assume_role_arn: isEditMode ? "**********" : "",
  };

  // Update form when existingConfig changes
  useEffect(() => {
    if (existingConfig) {
      const newValues = {
        email_from: existingConfig.details?.email_from || "",
        domain: existingConfig.details?.domain || "",
        aws_region: existingConfig.details?.aws_region || "",
        auth_method: "**********", // Always show placeholder in edit mode
        aws_access_key_id: "**********",
        aws_secret_access_key: "**********",
        aws_assume_role_arn: "**********",
      };
      form.setFieldsValue(newValues);
      setAuthMethod("**********"); // Set auth method state for edit mode
      setIsDirty(false); // Reset dirty state when loading existing config
    }
  }, [existingConfig, form]);

  // Check verification status using actual config data like the table does
  const getVerificationStatus = () => {
    // First preference: local verification data
    const localData = getVerificationData(messagingProviders.aws_ses);
    if (localData) {
      if (!localData.success) {
        return { isVerified: false, status: "Verify configuration" } as const;
      }
      const testTime = new Date(localData.timestamp);
      const formattedDistance = formatDistance(testTime, new Date(), {
        addSuffix: true,
      });
      return {
        isVerified: true,
        status: `Verified ${formattedDistance}`,
        timestamp: localData.timestamp,
      } as const;
    }

    // Next preference: backend data
    if (existingConfig) {
      const {
        last_test_succeeded: lastTestSucceeded,
        last_test_timestamp: lastTestTimestamp,
      } = existingConfig;

      if (lastTestTimestamp) {
        const testTime = new Date(lastTestTimestamp);
        const formattedDistance = formatDistance(testTime, new Date(), {
          addSuffix: true,
        });
        return {
          isVerified: lastTestSucceeded,
          status: lastTestSucceeded
            ? `Verified ${formattedDistance}`
            : "Verify configuration",
          timestamp: lastTestTimestamp,
        } as const;
      }
    }

    // Fallback to router query values (from table navigation)
    const querySucceededRaw = router.query.last_test_succeeded as
      | string
      | undefined;
    const queryTimestamp = router.query.last_test_timestamp as
      | string
      | undefined;
    if (queryTimestamp) {
      const succeeded =
        querySucceededRaw === "true" || querySucceededRaw === "1";
      const testTime = new Date(queryTimestamp);
      const formattedDistance = formatDistance(testTime, new Date(), {
        addSuffix: true,
      });
      return {
        isVerified: succeeded,
        status: succeeded
          ? `Verified ${formattedDistance}`
          : "Verify configuration",
        timestamp: queryTimestamp,
      } as const;
    }

    return { isVerified: false, status: "Verify configuration" } as const;
  };

  const verificationStatus = getVerificationStatus();

  // Exclude secrets that haven't changed from placeholder values
  const excludeUnchangedSecrets = (secretsValues: any) =>
    omitBy(
      mapValues(secretsValues, (value) => {
        // Don't send placeholder values
        return isEditMode && value === "**********" ? undefined : value;
      }),
      isUndefined,
    );

  // Custom validator to ensure either email_from or domain is provided
  const validateAwsSesConfig = useCallback(() => {
    const formValues = form.getFieldsValue();
    const emailFrom = formValues.email_from;
    const { domain } = formValues;

    // Check if values are provided and not empty
    const hasEmailFrom = emailFrom && emailFrom.trim() !== "";
    const hasDomain = domain && domain.trim() !== "";

    // At least one must be provided
    if (!hasEmailFrom && !hasDomain) {
      return Promise.reject(
        new Error("Either email from or domain must be provided"),
      );
    }

    return Promise.resolve();
  }, [form]);

  const handleAwsSesConfiguration = async (values: {
    email_from: string;
    domain: string;
    aws_region: string;
    auth_method: string;
    aws_access_key_id: string;
    aws_secret_access_key: string;
    aws_assume_role_arn: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update details if changed
        const currentEmailFrom = existingConfig?.details?.email_from || "";
        const currentDomain = existingConfig?.details?.domain || "";
        const currentAwsRegion = existingConfig?.details?.aws_region || "";

        const detailsChanged =
          values.email_from !== currentEmailFrom ||
          values.domain !== currentDomain ||
          values.aws_region !== currentAwsRegion;

        if (detailsChanged) {
          promises.push(
            updateMessagingConfiguration({
              key: configKey,
              config: {
                key: existingConfig?.key || configKey,
                name: existingConfig?.name,
                service_type:
                  existingConfig?.service_type || messagingProviders.aws_ses,
                details: {
                  ...existingConfig?.details,
                  email_from: values.email_from || null,
                  domain: values.domain || null,
                  aws_region: values.aws_region,
                },
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const secretsToUpdate = {
          auth_method: values.auth_method,
          aws_access_key_id: values.aws_access_key_id,
          aws_secret_access_key: values.aws_secret_access_key,
          aws_assume_role_arn: values.aws_assume_role_arn,
        };

        const newSecrets = excludeUnchangedSecrets(secretsToUpdate);
        if (!isEmpty(newSecrets)) {
          promises.push(
            updateMessagingSecrets({
              key: configKey,
              secrets: newSecrets,
            }),
          );
        }

        if (promises.length === 0) {
          message.info("No changes to save.");
          return;
        }

        const results = await Promise.all(promises);
        const hasError = results.some((result) => isErrorResult(result));

        if (hasError) {
          const errorResult = results.find((result) => isErrorResult(result));
          handleError(errorResult?.error);
        } else {
          message.success("AWS SES configuration successfully updated.");
          setIsDirty(false);
          // Refetch to get updated data
          if (refetchConfig) {
            refetchConfig();
          }
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.aws_ses,
          details: {
            email_from: values.email_from || null,
            domain: values.domain || null,
            aws_region: values.aws_region,
          },
          secrets: {
            auth_method: values.auth_method,
            aws_access_key_id: values.aws_access_key_id,
            aws_secret_access_key: values.aws_secret_access_key,
            aws_assume_role_arn: values.aws_assume_role_arn,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          message.success("AWS SES configuration successfully created.");
          setIsDirty(false);
          // Redirect to edit page with the created config key
          const createdConfigKey = result.data?.key;
          if (createdConfigKey) {
            const editPath = MESSAGING_PROVIDERS_EDIT_ROUTE.replace(
              "[key]",
              createdConfigKey,
            );
            router.push(editPath);
          } else {
            router.push(MESSAGING_PROVIDERS_ROUTE);
          }
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const handleVerifyConfiguration = async () => {
    try {
      const success = await verifyConfiguration(messagingProviders.aws_ses);
      if (success && refetchConfig) {
        // Add a small delay to allow backend to update the record
        setTimeout(() => {
          refetchConfig();
        }, 500);
      }
    } catch (error) {
      handleError(error);
    }
  };

  const handleFormValuesChange = (changedValues: any, allValues: any) => {
    // Compare current values with initial values, accounting for placeholders
    const currentValues = { ...allValues };
    const compareValues = { ...initialValues };

    // If in edit mode and secret fields haven't changed from placeholder, consider them unchanged
    if (isEditMode) {
      Object.keys(currentValues).forEach((key) => {
        if (currentValues[key] === "**********") {
          currentValues[key] = compareValues[key as keyof typeof compareValues];
        }
      });
    }

    // Track auth method changes
    if (changedValues.auth_method !== undefined) {
      setAuthMethod(changedValues.auth_method);

      // If auth method changed to automatic, clear secret key fields
      if (changedValues.auth_method === "automatic") {
        form.setFieldsValue({
          aws_access_key_id: "",
          aws_secret_access_key: "",
        });
      }
    }

    setIsDirty(!isEqual(currentValues, compareValues));
  };

  const handleFieldChange = () => {
    // Trigger validation on both email_from and domain fields
    // when either one changes, since they have interdependent validation
    form.validateFields(["email_from", "domain"]).catch(() => {
      // Ignore validation errors here as they'll be shown in the UI
    });
  };

  return (
    <Box position="relative">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleAwsSesConfiguration}
        onValuesChange={handleFormValuesChange}
      >
        <Box
          maxWidth="720px"
          border="1px"
          borderColor="gray.200"
          borderRadius={6}
          overflow="visible"
          mt={6}
        >
          <Box
            backgroundColor="gray.50"
            px={6}
            py={4}
            display="flex"
            flexDirection="row"
            alignItems="center"
            borderBottom="1px"
            borderColor="gray.200"
            borderTopRadius={6}
          >
            <HStack>
              <AwsIcon />
              <Heading as="h3" size="xs">
                AWS SES email messaging configuration
              </Heading>
            </HStack>
          </Box>

          <Box px={6} py={6}>
            <Form.Item
              name="email_from"
              label="Email from"
              rules={[{ validator: validateAwsSesConfig }]}
              style={{ marginBottom: 24 }}
            >
              <Input
                placeholder={
                  isEditMode ? "Enter new email from" : "Enter email from"
                }
                onChange={() => handleFieldChange()}
              />
            </Form.Item>

            <Form.Item
              name="domain"
              label="Domain"
              rules={[{ validator: validateAwsSesConfig }]}
              style={{ marginBottom: 24 }}
            >
              <Input
                placeholder={isEditMode ? "Enter new domain" : "Enter domain"}
                onChange={() => handleFieldChange()}
              />
            </Form.Item>

            <Form.Item
              name="aws_region"
              label="AWS region"
              rules={[{ required: true, message: "AWS region is required" }]}
              style={{ marginBottom: 24 }}
            >
              <Input
                placeholder={
                  isEditMode
                    ? "Enter new AWS region"
                    : "Enter AWS region (e.g., us-east-1)"
                }
              />
            </Form.Item>

            <Form.Item
              name="auth_method"
              label="Authentication method"
              rules={[
                {
                  required: true,
                  message: "Authentication method is required",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Select
                placeholder="Select authentication method"
                options={[
                  {
                    label: "Secret keys",
                    value: "secret_keys",
                  },
                  {
                    label: "Automatic",
                    value: "automatic",
                  },
                ]}
              />
            </Form.Item>

            {/* Only show AWS credentials fields for secret_keys auth method */}
            {(authMethod === "secret_keys" ||
              (isEditMode && authMethod === "**********")) && (
              <>
                <Form.Item
                  name="aws_access_key_id"
                  label="AWS access key ID"
                  rules={
                    authMethod === "secret_keys" ||
                    (isEditMode && authMethod === "**********")
                      ? [
                          {
                            required: true,
                            message:
                              "AWS access key ID is required for secret keys authentication",
                          },
                        ]
                      : []
                  }
                  style={{ marginBottom: 24 }}
                >
                  <Input.Password
                    placeholder={
                      isEditMode
                        ? "Enter new AWS access key ID"
                        : "Enter AWS access key ID"
                    }
                  />
                </Form.Item>

                <Form.Item
                  name="aws_secret_access_key"
                  label="AWS secret access key"
                  rules={
                    authMethod === "secret_keys" ||
                    (isEditMode && authMethod === "**********")
                      ? [
                          {
                            required: true,
                            message:
                              "AWS secret access key is required for secret keys authentication",
                          },
                        ]
                      : []
                  }
                  style={{ marginBottom: 24 }}
                >
                  <Input.Password
                    placeholder={
                      isEditMode
                        ? "Enter new AWS secret access key"
                        : "Enter AWS secret access key"
                    }
                  />
                </Form.Item>
              </>
            )}

            <Form.Item name="aws_assume_role_arn" label="AWS assume role ARN">
              <Input.Password
                placeholder={
                  isEditMode
                    ? "Enter new AWS assume role ARN"
                    : "Enter AWS assume role ARN (optional)"
                }
              />
            </Form.Item>

            <Box mt={6} className="flex justify-between">
              <Box>
                {isEditMode && verificationStatus.isVerified && (
                  <Button
                    type="default"
                    onClick={() => setIsTestMessageModalOpen(true)}
                    data-testid="send-test-message-btn"
                  >
                    Send test email
                  </Button>
                )}
              </Box>
              <Box className="flex">
                {isEditMode ? (
                  <Button
                    onClick={handleVerifyConfiguration}
                    className="mr-2"
                    data-testid="test-btn"
                    loading={isVerifying}
                    icon={
                      verificationStatus.isVerified && !isVerifying ? (
                        <GreenCheckCircleIcon />
                      ) : undefined
                    }
                  >
                    {(() => {
                      if (isVerifying) {
                        return "Verifying";
                      }
                      if (verificationStatus.isVerified) {
                        return "Verified";
                      }
                      return verificationStatus.status;
                    })()}
                  </Button>
                ) : (
                  <Button
                    onClick={() => router.push(MESSAGING_PROVIDERS_ROUTE)}
                    className="mr-2"
                  >
                    Cancel
                  </Button>
                )}
                <Button
                  htmlType="submit"
                  type="primary"
                  data-testid="save-btn"
                  disabled={!isDirty}
                >
                  Save
                </Button>
              </Box>
            </Box>
          </Box>
        </Box>
      </Form>

      {/* Send test message modal */}
      <SendTestMessageModal
        serviceType={messagingProviders.aws_ses}
        isOpen={isTestMessageModalOpen}
        onClose={() => setIsTestMessageModalOpen(false)}
      />
    </Box>
  );
};

export default AwsSesMessagingForm;
