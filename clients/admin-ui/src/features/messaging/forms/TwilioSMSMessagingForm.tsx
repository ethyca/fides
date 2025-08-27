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
import { useCallback, useEffect, useState } from "react";

import {
  isErrorResult,
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";
import {
  MESSAGING_PROVIDERS_EDIT_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
} from "~/features/common/nav/routes";
import TwilioIcon from "~/features/messaging/icons/TwilioIcon";

import { messagingProviders } from "../constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "../messaging.slice";
import { SendTestMessageModal } from "../SendTestMessageModal";
import { useVerifyConfiguration } from "../useVerifyConfiguration";

interface TwilioSMSMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

// NOTE: All Twilio SMS fields (Account SID, Message service SID, phone number, and auth token)
// are stored as secrets in the backend. Since the API doesn't return secret values for security,
// all fields are treated as password inputs for consistency. Ideally, Account SID, Message service SID,
// and phone number should be non-sensitive and stored in the details section instead of secrets.

const TwilioSMSMessagingForm = ({ configKey }: TwilioSMSMessagingFormProps) => {
  const router = useRouter();
  const { verifyConfiguration, isVerifying, getVerificationData } =
    useVerifyConfiguration();
  const [isTestMessageModalOpen, setIsTestMessageModalOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [form] = Form.useForm();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Fetch existing config data in edit mode
  const { data: existingConfig, refetch: refetchConfig } =
    useGetMessagingConfigurationByKeyQuery(
      { key: configKey! },
      { skip: !configKey },
    );

  // Memoized initial values
  const initialValues = {
    // NOTE: All Twilio SMS fields are stored as secrets in the backend,
    // and the API doesn't return secret values. All fields use placeholder
    // values in edit mode and are treated consistently as password inputs.
    account_sid: isEditMode ? "**********" : "",
    auth_token: isEditMode ? "**********" : "",
    messaging_service_sid: isEditMode ? "**********" : "",
    phone: isEditMode ? "**********" : "",
  };

  // Update form when existingConfig changes
  useEffect(() => {
    if (existingConfig) {
      const newValues = {
        account_sid: "**********", // Always show placeholder in edit mode
        auth_token: "**********",
        messaging_service_sid: "**********",
        phone: "**********",
      };
      form.setFieldsValue(newValues);
      setIsDirty(false); // Reset dirty state when loading existing config
    }
  }, [existingConfig, form]);

  // Check verification status using actual config data like the table does
  const getVerificationStatus = () => {
    // First preference: local verification data
    const localData = getVerificationData(messagingProviders.twilio_text);
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

  // Helper function to extract error message using the same logic as useAPIHelper
  const getErrorMessage = (error: any) => {
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0].msg;
    }
    return errorMsg;
  };

  // Custom validator to ensure either messaging service SID or phone number is provided
  const validateTwilioConfig = useCallback(() => {
    const formValues = form.getFieldsValue();
    const messagingServiceSid = formValues.messaging_service_sid;
    const phoneNumber = formValues.phone;

    // Check if values are provided and not just placeholders
    const hasMessagingService =
      messagingServiceSid &&
      messagingServiceSid.trim() !== "" &&
      messagingServiceSid !== "**********";
    const hasPhoneNumber =
      phoneNumber && phoneNumber.trim() !== "" && phoneNumber !== "**********";

    // At least one must be provided
    if (!hasMessagingService && !hasPhoneNumber) {
      return Promise.reject(
        new Error(
          "Either messaging service SID or phone number must be provided",
        ),
      );
    }

    return Promise.resolve();
  }, [form]);

  const handleTwilioSMSConfiguration = async (values: {
    account_sid: string;
    auth_token: string;
    messaging_service_sid: string;
    phone: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: only update secrets that aren't placeholders
        const secretsToUpdate = {
          twilio_account_sid: values.account_sid,
          twilio_auth_token: values.auth_token,
          twilio_messaging_service_sid: values.messaging_service_sid,
          twilio_sender_phone_number: values.phone,
        };

        const newSecrets = excludeUnchangedSecrets(secretsToUpdate);

        if (isEmpty(newSecrets)) {
          message.info("No changes to save.");
          return;
        }

        const result = await updateMessagingSecrets({
          key: configKey,
          secrets: newSecrets,
        });

        if (isErrorResult(result)) {
          message.error(getErrorMessage(result.error));
        } else {
          message.success("Twilio SMS configuration successfully updated.");
          setIsDirty(false);
          // Refetch to get updated data
          if (refetchConfig) {
            refetchConfig();
          }
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.twilio_text,
          secrets: {
            twilio_account_sid: values.account_sid,
            twilio_auth_token: values.auth_token,
            twilio_messaging_service_sid: values.messaging_service_sid,
            twilio_sender_phone_number: values.phone,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          message.error(getErrorMessage(result.error));
        } else {
          message.success("Twilio SMS configuration successfully created.");
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
      console.error("Error in handleTwilioSMSConfiguration:", error);
      message.error("An unexpected error occurred. Please try again.");
    }
  };

  const handleVerifyConfiguration = async () => {
    try {
      const success = await verifyConfiguration(messagingProviders.twilio_text);
      if (success && refetchConfig) {
        // Add a small delay to allow backend to update the record
        setTimeout(() => {
          console.log("Refetching config after verification...");
          refetchConfig();
        }, 500);
      }
    } catch (error) {
      console.error("Error Verifying:", error);
      message.error("An unexpected error occurred during verification.");
    }
  };

  const handleFormValuesChange = (changedValues: any, allValues: any) => {
    // Compare current values with initial values, accounting for placeholders
    const currentValues = { ...allValues };
    const compareValues = { ...initialValues };

    // If in edit mode and any field hasn't changed from placeholder, consider it unchanged
    if (isEditMode) {
      Object.keys(currentValues).forEach((key) => {
        if (currentValues[key] === "**********") {
          currentValues[key] = compareValues[key as keyof typeof compareValues];
        }
      });
    }

    setIsDirty(!isEqual(currentValues, compareValues));
  };

  const handleFieldChange = () => {
    // Trigger validation on both messaging_service_sid and phone fields
    // when either one changes, since they have interdependent validation
    form.validateFields(["messaging_service_sid", "phone"]).catch(() => {
      // Ignore validation errors here as they'll be shown in the UI
    });
  };

  return (
    <Box position="relative">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleTwilioSMSConfiguration}
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
              <TwilioIcon />
              <Heading as="h3" size="xs">
                Twilio SMS messaging configuration
              </Heading>
            </HStack>
          </Box>

          <Box px={6} py={6}>
            <Form.Item
              name="account_sid"
              label="Account SID"
              rules={[
                { required: true, message: "Account SID is required" },
                {
                  type: "string",
                  min: 1,
                  message: "Account SID cannot be empty",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input.Password
                placeholder={
                  isEditMode ? "Enter new account SID" : "Enter account SID"
                }
              />
            </Form.Item>

            <Form.Item
              name="auth_token"
              label="Auth token"
              rules={[
                { required: true, message: "Auth token is required" },
                {
                  type: "string",
                  min: 1,
                  message: "Auth token cannot be empty",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input.Password
                placeholder={
                  isEditMode ? "Enter new auth token" : "Enter auth token"
                }
              />
            </Form.Item>

            <Form.Item
              name="messaging_service_sid"
              label="Messaging service SID"
              rules={[{ validator: validateTwilioConfig }]}
              style={{ marginBottom: 24 }}
            >
              <Input.Password
                placeholder={
                  isEditMode
                    ? "Enter new messaging service SID"
                    : "Enter messaging service SID"
                }
                onChange={() => handleFieldChange()}
              />
            </Form.Item>

            <Form.Item
              name="phone"
              label="Phone number"
              rules={[{ validator: validateTwilioConfig }]}
            >
              <Input.Password
                placeholder={
                  isEditMode ? "Enter new phone number" : "Enter phone number"
                }
                onChange={() => handleFieldChange()}
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
                    Send test SMS
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
        serviceType={messagingProviders.twilio_text}
        isOpen={isTestMessageModalOpen}
        onClose={() => setIsTestMessageModalOpen(false)}
      />
    </Box>
  );
};

export default TwilioSMSMessagingForm;
