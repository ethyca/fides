import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  Box,
  Heading,
  HStack,
} from "fidesui";
import { isEmpty, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useState } from "react";

import {
  isErrorResult,
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";
import {
  MESSAGING_PROVIDERS_EDIT_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
} from "~/features/common/nav/routes";
import { TestMessagingProviderModal } from "~/features/messaging/TestMessagingProviderModal";
import TwilioIcon from "~/features/messaging/TwilioIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";

interface TwilioSMSMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

// NOTE: All Twilio SMS fields (Account SID, Message service SID, phone number, and auth token)
// are stored as secrets in the backend. Since the API doesn't return secret values for security,
// all fields are treated as password inputs for consistency. Ideally, Account SID, Message service SID,
// and phone number should be non-sensitive and stored in the details section instead of secrets.

const TwilioSMSMessagingForm = ({ configKey }: TwilioSMSMessagingFormProps) => {
  const router = useRouter();
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [form] = Form.useForm();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Fetch existing config data in edit mode
  useGetMessagingConfigurationByKeyQuery(
    { key: configKey! },
    { skip: !configKey },
  );

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
      message.error("An unexpected error occurred. Please try again.");
    }
  };

  // Custom validator to ensure either messaging service SID or phone number is provided
  const validateTwilioConfig = () => {
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
  };

  const initialValues = {
    // NOTE: All Twilio SMS fields are stored as secrets in the backend,
    // and the API doesn't return secret values. All fields use placeholder
    // values in edit mode and are treated consistently as password inputs.
    account_sid: isEditMode ? "**********" : "",
    auth_token: isEditMode ? "**********" : "",
    messaging_service_sid: isEditMode ? "**********" : "",
    phone: isEditMode ? "**********" : "",
  };

  return (
    <Box>
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleTwilioSMSConfiguration}
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
                onChange={() => {
                  // Trigger validation on the phone field when this changes
                  form.validateFields(["phone"]);
                }}
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
                onChange={() => {
                  // Trigger validation on the messaging_service_sid field when this changes
                  form.validateFields(["messaging_service_sid"]);
                }}
              />
            </Form.Item>

            <Box mt={6}>
              {isEditMode ? (
                <Button
                  onClick={() => setIsTestModalOpen(true)}
                  className="mr-2"
                  data-testid="test-btn"
                >
                  Test configuration
                </Button>
              ) : (
                <Button
                  onClick={() => router.push(MESSAGING_PROVIDERS_ROUTE)}
                  className="mr-2"
                >
                  Cancel
                </Button>
              )}
              <Button htmlType="submit" type="primary" data-testid="save-btn">
                Save
              </Button>
            </Box>
          </Box>
        </Box>
      </Form>

      {isEditMode && (
        <TestMessagingProviderModal
          serviceType={messagingProviders.twilio_text}
          isOpen={isTestModalOpen}
          onClose={() => setIsTestModalOpen(false)}
        />
      )}
    </Box>
  );
};

export default TwilioSMSMessagingForm;
