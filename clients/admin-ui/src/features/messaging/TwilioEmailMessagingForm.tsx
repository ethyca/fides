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

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
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
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";

interface TwilioEmailMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const TwilioEmailMessagingForm = ({
  configKey,
}: TwilioEmailMessagingFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [form] = Form.useForm();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingConfiguration] =
    useUpdateMessagingConfigurationByKeyMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Fetch existing config data in edit mode
  const { data: existingConfig } = useGetMessagingConfigurationByKeyQuery(
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

  const handleTwilioEmailConfiguration = async (values: {
    email: string;
    twilio_api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update email if changed
        const currentEmail = existingConfig?.details?.twilio_email_from || "";
        if (values.email !== currentEmail && values.email.trim() !== "") {
          promises.push(
            updateMessagingConfiguration({
              key: configKey,
              config: {
                key: existingConfig?.key || configKey,
                name: existingConfig?.name,
                service_type:
                  existingConfig?.service_type ||
                  messagingProviders.twilio_email,
                details: {
                  ...existingConfig?.details,
                  twilio_email_from: values.email,
                },
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({
          api_key: values.twilio_api_key,
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
          message.success("Twilio email configuration successfully updated.");
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.twilio_email,
          details: {
            twilio_email_from: values.email,
          },
          secrets: {
            api_key: values.twilio_api_key,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          message.success("Twilio email configuration successfully created.");
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

  const initialValues = {
    email: existingConfig?.details?.twilio_email_from || "",
    twilio_api_key: isEditMode ? "**********" : "",
  };

  return (
    <Box>
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleTwilioEmailConfiguration}
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
                Twilio email messaging configuration
              </Heading>
            </HStack>
          </Box>

          <Box px={6} py={6}>
            <Form.Item
              name="email"
              label="Email"
              rules={[
                { required: true, message: "Email is required" },
                { type: "email", message: "Please enter a valid email" },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input
                placeholder={isEditMode ? "Enter new email" : "Enter email"}
              />
            </Form.Item>

            <Form.Item
              name="twilio_api_key"
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
          serviceType={messagingProviders.twilio_email}
          isOpen={isTestModalOpen}
          onClose={() => setIsTestModalOpen(false)}
        />
      )}
    </Box>
  );
};

export default TwilioEmailMessagingForm;
