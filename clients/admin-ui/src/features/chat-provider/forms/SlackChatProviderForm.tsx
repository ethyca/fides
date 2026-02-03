import {
  Button,
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraHStack as HStack,
  ChakraText as Text,
  Form,
  GreenCheckCircleIcon,
  Input,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import {
  ChatProviderConfigCreate,
  ChatProviderConfigUpdate,
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
  useUpdateChatConfigMutation,
} from "../chatProvider.slice";
import SlackIcon from "../icons/SlackIcon";

interface SlackChatProviderFormProps {
  configId?: string;
}

const SlackChatProviderForm = ({ configId }: SlackChatProviderFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const message = useMessage();
  const [form] = Form.useForm();
  const [isDirty, setIsDirty] = useState(false);

  // Fetch existing config if editing
  const { data: existingConfig, refetch } = useGetChatConfigQuery(configId!, {
    skip: !configId,
  });
  const [createConfig] = useCreateChatConfigMutation();
  const [updateConfig] = useUpdateChatConfigMutation();

  const isEditMode = !!configId;
  const isAuthorized = !!existingConfig?.authorized;

  // Check for OAuth callback results in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const chatSuccess = urlParams.get("chat_success");
    const chatError = urlParams.get("chat_error");

    if (chatSuccess === "true") {
      message.success("Slack authorization successful!");
      refetch();
      // Clean up URL but keep id param
      const newUrl = configId
        ? `${window.location.pathname}?id=${configId}`
        : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    } else if (chatError) {
      const errorMessages: Record<string, string> = {
        invalid_state:
          "Authorization failed: Invalid state token. Please try again.",
        not_configured: "Authorization failed: Chat provider not configured.",
        token_failed: "Authorization failed: Could not obtain access token.",
        no_token: "Authorization failed: No token received from Slack.",
      };
      message.error(
        errorMessages[chatError] || "Authorization failed. Please try again.",
      );
      // Clean up URL but keep id param
      const newUrl = configId
        ? `${window.location.pathname}?id=${configId}`
        : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
  }, [refetch, message, configId]);

  const hasSigningSecret = existingConfig?.has_signing_secret;

  const initialValues = {
    workspace_url: existingConfig?.workspace_url || "",
    client_id: existingConfig?.client_id || "",
    client_secret: isEditMode ? "**********" : "",
    signing_secret: isEditMode && hasSigningSecret ? "**********" : "",
  };

  // Update form when existingConfig changes
  useEffect(() => {
    if (existingConfig) {
      form.setFieldsValue({
        workspace_url: existingConfig.workspace_url || "",
        client_id: existingConfig.client_id || "",
        client_secret: "**********",
        signing_secret: existingConfig.has_signing_secret ? "**********" : "",
      });
      setIsDirty(false);
    }
  }, [existingConfig, form]);

  const handleSubmit = async (values: {
    workspace_url: string;
    client_id: string;
    client_secret: string;
    signing_secret: string;
  }) => {
    try {
      if (isEditMode && configId) {
        // Update existing config
        const payload: ChatProviderConfigUpdate = {
          workspace_url: values.workspace_url || undefined,
          client_id: values.client_id || undefined,
          // Only send secrets if they're not the placeholder
          client_secret:
            values.client_secret && values.client_secret !== "**********"
              ? values.client_secret
              : undefined,
          signing_secret:
            values.signing_secret && values.signing_secret !== "**********"
              ? values.signing_secret
              : undefined,
        };

        const result = await updateConfig({ configId, data: payload });

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          message.success("Slack configuration saved successfully.");
          setIsDirty(false);
          refetch();
          // Reset form with current values but clear the secrets
          form.setFieldsValue({
            ...values,
            client_secret: "**********",
            signing_secret: values.signing_secret ? "**********" : "",
          });
        }
      } else {
        // Create new config
        const payload: ChatProviderConfigCreate = {
          provider_type: "slack",
          workspace_url: values.workspace_url,
          client_id: values.client_id || undefined,
          client_secret: values.client_secret || undefined,
          signing_secret: values.signing_secret || undefined,
        };

        const result = await createConfig(payload);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else if ("data" in result && result.data) {
          message.success("Slack configuration created successfully.");
          // Redirect to edit mode with the new config ID
          router.push(`${CHAT_PROVIDERS_ROUTE}/configure?id=${result.data.id}`);
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const handleAuthorize = () => {
    const authorizeUrl = configId
      ? `/api/v1/plus/chat/authorize?config_id=${configId}`
      : "/api/v1/plus/chat/authorize";
    window.location.href = authorizeUrl;
  };

  const handleFormValuesChange = () => {
    const currentValues = form.getFieldsValue();
    const hasChanges =
      currentValues.workspace_url !== initialValues.workspace_url ||
      currentValues.client_id !== initialValues.client_id ||
      (currentValues.client_secret !== "**********" &&
        currentValues.client_secret !== "") ||
      (currentValues.signing_secret !== "**********" &&
        currentValues.signing_secret !== "" &&
        currentValues.signing_secret !== initialValues.signing_secret);
    setIsDirty(hasChanges);
  };

  // If already authorized, show as verified immediately
  const isFullyAuthorized = isAuthorized;

  return (
    <Box position="relative">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleSubmit}
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
              <SlackIcon />
              <Heading as="h3" size="xs">
                Slack chat provider configuration
              </Heading>
            </HStack>
          </Box>

          <Box px={6} py={6}>
            <Form.Item
              name="workspace_url"
              label="Workspace URL"
              rules={[
                { required: true, message: "Workspace URL is required" },
                {
                  type: "string",
                  min: 1,
                  message: "Workspace URL cannot be empty",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input placeholder="your-company.slack.com" />
            </Form.Item>

            <Form.Item
              name="client_id"
              label="Client ID"
              rules={[
                { required: true, message: "Client ID is required" },
                {
                  type: "string",
                  min: 1,
                  message: "Client ID cannot be empty",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input placeholder="Enter your Slack App Client ID" />
            </Form.Item>

            <Form.Item
              name="client_secret"
              label="Client secret"
              required
              rules={[
                {
                  required: !isEditMode,
                  message: "Client secret is required",
                },
              ]}
              style={{ marginBottom: 24 }}
            >
              <Input.Password
                placeholder={
                  isEditMode
                    ? "Enter new client secret to change"
                    : "Enter your Slack App Client Secret"
                }
              />
            </Form.Item>

            <Form.Item
              name="signing_secret"
              label="Signing secret"
              required
              tooltip="Used to verify that webhook events are from Slack. Found in your Slack App's Basic Information page."
              rules={[
                {
                  required: !isEditMode || !hasSigningSecret,
                  message: "Signing secret is required",
                },
              ]}
            >
              <Input.Password
                placeholder={
                  isEditMode && hasSigningSecret
                    ? "Enter new signing secret to change"
                    : "Enter your Slack App Signing Secret"
                }
              />
            </Form.Item>

            <Box mt={6} className="flex justify-end">
              <Box className="flex">
                {isEditMode ? (
                  <>
                    {/* Authorize button - show when not authorized */}
                    {!isAuthorized && (
                      <Button
                        onClick={handleAuthorize}
                        className="mr-2"
                        disabled={isDirty}
                        data-testid="authorize-chat-btn"
                      >
                        Authorize with Slack
                      </Button>
                    )}
                    {/* Authorized status - show when OAuth is complete */}
                    {isFullyAuthorized && (
                      <HStack className="mr-4" data-testid="authorize-status">
                        <GreenCheckCircleIcon />
                        <Text color="green.500" fontWeight="medium">
                          Authorized
                        </Text>
                      </HStack>
                    )}
                  </>
                ) : (
                  <Button
                    onClick={() => router.push(CHAT_PROVIDERS_ROUTE)}
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
    </Box>
  );
};

export default SlackChatProviderForm;
