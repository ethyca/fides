import { formatDistance } from "date-fns";
import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  Box,
  GreenCheckCircleIcon,
  Heading,
  HStack,
} from "fidesui";
import { isEmpty, isEqual, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import {
  MESSAGING_PROVIDERS_EDIT_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
} from "~/features/common/nav/routes";
import MailgunIcon from "~/features/messaging/icons/MailgunIcon";

import { messagingProviders } from "../constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "../messaging.slice";
import { SendTestMessageModal } from "../SendTestMessageModal";
import { useVerifyConfiguration } from "../useVerifyConfiguration";

interface MailgunMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const MailgunMessagingForm = ({ configKey }: MailgunMessagingFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const { verifyConfiguration, isVerifying, getVerificationData } =
    useVerifyConfiguration();
  const [isTestMessageModalOpen, setIsTestMessageModalOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [form] = Form.useForm();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingConfiguration] =
    useUpdateMessagingConfigurationByKeyMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Fetch existing config data in edit mode
  const { data: existingConfig, refetch: refetchConfig } =
    useGetMessagingConfigurationByKeyQuery(
      { key: configKey! },
      { skip: !configKey },
    );

  // Memoized initial values to prevent unnecessary re-renders
  const initialValues = {
    domain: existingConfig?.details?.domain || "",
    mailgun_api_key: isEditMode ? "**********" : "",
  };

  // Update form when existingConfig changes
  useEffect(() => {
    if (existingConfig) {
      const newValues = {
        domain: existingConfig.details?.domain || "",
        mailgun_api_key: "**********", // Always show placeholder in edit mode
      };
      form.setFieldsValue(newValues);
      setIsDirty(false); // Reset dirty state when loading existing config
    }
  }, [existingConfig, form]);

  const getVerificationStatus = () => {
    // Prefer local verification data first
    const verificationData = getVerificationData(messagingProviders.mailgun);
    if (verificationData) {
      if (!verificationData.success) {
        return { isVerified: false, status: "Verify configuration" } as const;
      }
      const testTime = new Date(verificationData.timestamp);
      const formattedDistance = formatDistance(testTime, new Date(), {
        addSuffix: true,
      });
      return {
        isVerified: true,
        status: `Verified ${formattedDistance}`,
        timestamp: verificationData.timestamp,
      } as const;
    }

    // Next, use backend data
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

  const handleMailgunConfiguration = async (values: {
    domain: string;
    mailgun_api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update domain if changed
        const currentDomain = existingConfig?.details?.domain || "";
        if (values.domain !== currentDomain && values.domain.trim() !== "") {
          promises.push(
            updateMessagingConfiguration({
              key: configKey,
              config: {
                key: existingConfig?.key || configKey,
                name: existingConfig?.name,
                service_type:
                  existingConfig?.service_type || messagingProviders.mailgun,
                details: {
                  ...existingConfig?.details,
                  is_eu_domain: "false",
                  domain: values.domain,
                },
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({
          mailgun_api_key: values.mailgun_api_key,
        });
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
          message.success("Mailgun configuration successfully updated.");
          setIsDirty(false);
          // Refetch to get updated data
          if (refetchConfig) {
            refetchConfig();
          }
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.mailgun,
          details: {
            is_eu_domain: "false",
            domain: values.domain,
          },
          secrets: {
            mailgun_api_key: values.mailgun_api_key,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          message.success("Mailgun configuration successfully created.");
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
      console.error("Error in handleMailgunConfiguration:", error);
      handleError(error);
    }
  };

  const handleVerifyConfiguration = async () => {
    try {
      const success = await verifyConfiguration(messagingProviders.mailgun);
      if (success && refetchConfig) {
        // Add a small delay to allow backend to update the record
        setTimeout(() => {
          console.log("Refetching config after verification...");
          refetchConfig();
        }, 500);
      }
    } catch (error) {
      console.error("Error Verifying:", error);
      handleError(error);
    }
  };

  const handleFormValuesChange = (changedValues: any, allValues: any) => {
    // Compare current values with initial values, accounting for placeholder
    const currentValues = { ...allValues };
    const compareValues = { ...initialValues };

    // If in edit mode and API key hasn't changed from placeholder, consider it unchanged
    if (isEditMode && currentValues.mailgun_api_key === "**********") {
      currentValues.mailgun_api_key = compareValues.mailgun_api_key;
    }

    setIsDirty(!isEqual(currentValues, compareValues));
  };

  return (
    <Box position="relative">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleMailgunConfiguration}
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
              <MailgunIcon />
              <Heading as="h3" size="xs">
                Mailgun email messaging configuration
              </Heading>
            </HStack>
          </Box>

          <Box px={6} py={6}>
            <Form.Item
              name="domain"
              label="Domain"
              rules={[
                { required: true, message: "Domain is required" },
                { type: "string", min: 1, message: "Domain cannot be empty" },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input
                placeholder={isEditMode ? "Enter new domain" : "Enter domain"}
              />
            </Form.Item>

            <Form.Item
              name="mailgun_api_key"
              label="API key"
              rules={[
                { required: true, message: "API key is required" },
                { type: "string", min: 1, message: "API key cannot be empty" },
              ]}
            >
              <Input.Password
                placeholder={isEditMode ? "Enter new API key" : "Enter API key"}
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
        serviceType={messagingProviders.mailgun}
        isOpen={isTestMessageModalOpen}
        onClose={() => setIsTestMessageModalOpen(false)}
      />
    </Box>
  );
};

export default MailgunMessagingForm;
