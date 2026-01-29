import {
  Button,
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraStack as Stack,
  ChakraText as Text,
  useChakraToast as useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useEffect, useState } from "react";
import * as Yup from "yup";

import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  ChatProviderSettings,
  useGetChatSettingsQuery,
  useTestChatConnectionMutation,
  useUpdateChatSettingsMutation,
} from "./chatProvider.slice";

interface ChatProviderFormValues {
  enabled: boolean;
  workspace_url: string;
  client_id: string;
  client_secret: string;
}

const ChatProviderValidationSchema = Yup.object().shape({
  enabled: Yup.boolean(),
  workspace_url: Yup.string().when("enabled", {
    is: true,
    then: (schema) => schema.required("Workspace URL is required"),
  }),
  client_id: Yup.string().when("enabled", {
    is: true,
    then: (schema) => schema.required("Client ID is required"),
  }),
  client_secret: Yup.string(),
});

const ChatProviderSection = () => {
  const { data: settings, isLoading, isError, refetch } = useGetChatSettingsQuery();
  const [updateSettings] = useUpdateChatSettingsMutation();
  const [testConnection, { isLoading: isTesting }] =
    useTestChatConnectionMutation();
  const toast = useToast();
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Check for OAuth callback results in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const chatSuccess = urlParams.get("chat_success");
    const chatError = urlParams.get("chat_error");

    if (chatSuccess === "true") {
      toast(successToastParams("Slack authorization successful!"));
      refetch();
      // Clean up URL
      window.history.replaceState({}, "", window.location.pathname);
    } else if (chatError) {
      const errorMessages: Record<string, string> = {
        invalid_state: "Authorization failed: Invalid state token. Please try again.",
        not_configured: "Authorization failed: Chat provider not configured.",
        token_failed: "Authorization failed: Could not obtain access token.",
        no_token: "Authorization failed: No token received from Slack.",
      };
      toast(
        errorToastParams(
          errorMessages[chatError] || "Authorization failed. Please try again."
        )
      );
      // Clean up URL
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [refetch, toast]);

  const initialValues: ChatProviderFormValues = {
    enabled: settings?.enabled ?? false,
    workspace_url: settings?.workspace_url ?? "",
    client_id: settings?.client_id ?? "",
    client_secret: "",
  };

  const handleSubmit = async (
    values: ChatProviderFormValues,
    formikHelpers: FormikHelpers<ChatProviderFormValues>
  ) => {
    const payload: ChatProviderSettings = {
      enabled: values.enabled,
      provider_type: "slack",
      workspace_url: values.workspace_url || undefined,
      client_id: values.client_id || undefined,
      client_secret: values.client_secret || undefined,
    };

    const result = await updateSettings(payload);

    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        "An error occurred while saving settings."
      );
      toast(errorToastParams(errorMsg));
    } else {
      toast(successToastParams("Chat provider settings saved."));
      setHasUnsavedChanges(false);
      formikHelpers.resetForm({
        values: {
          ...values,
          client_secret: "", // Clear secret after save
        },
      });
    }
  };

  const handleTestConnection = async () => {
    const result = await testConnection();

    if ("data" in result && result.data) {
      if (result.data.success) {
        toast(successToastParams(result.data.message));
      } else {
        toast(errorToastParams(result.data.message));
      }
    } else if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        "Connection test failed."
      );
      toast(errorToastParams(errorMsg));
    }
  };

  const handleAuthorize = () => {
    // Open authorization in the same window
    window.location.href = "/api/v1/plus/chat/authorize";
  };

  if (isLoading) {
    return (
      <Box maxWidth="600px" marginTop="40px">
        <Heading marginBottom={4} fontSize="lg">
          Slack integration
        </Heading>
        <Text>Loading...</Text>
      </Box>
    );
  }

  // Show section even if API fails (endpoint may not exist yet)
  if (isError) {
    return (
      <Box maxWidth="600px" marginTop="40px">
        <Heading marginBottom={4} fontSize="lg">
          Slack integration
        </Heading>
        <Text fontSize="sm" color="gray.500">
          Chat provider settings are not available. The backend may need to be
          updated with the latest code.
        </Text>
      </Box>
    );
  }

  return (
    <Box maxWidth="600px" marginTop="40px">
      <Heading marginBottom={4} fontSize="lg">
        Slack integration
      </Heading>
      <Text marginBottom="30px" fontSize="sm">
        Connect your Slack workspace to enable notifications and alerts.
        Microsoft Teams support coming soon.
      </Text>

      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={ChatProviderValidationSchema}
      >
        {({ dirty, isValid, values, isSubmitting }) => (
          <Form data-testid="chat-provider-form">
            <Stack spacing={4}>
              <CustomSwitch
                id="enabled"
                name="enabled"
                label="Enable Slack integration"
              />

              {values.enabled && (
                <>
                  <CustomTextInput
                    id="workspace_url"
                    name="workspace_url"
                    label="Workspace URL"
                    placeholder="your-company.slack.com"
                    tooltip="Your Slack workspace URL"
                    variant="stacked"
                    isRequired
                  />
                  <CustomTextInput
                    id="client_id"
                    name="client_id"
                    label="Client ID"
                    tooltip="Client ID from your Slack App"
                    variant="stacked"
                    isRequired
                  />
                  <CustomTextInput
                    id="client_secret"
                    name="client_secret"
                    label="Client secret"
                    type="password"
                    tooltip="Client secret from your Slack App (leave blank to keep existing)"
                    placeholder={settings?.client_id ? "••••••••" : ""}
                    variant="stacked"
                  />

                  <Box>
                    <Button
                      htmlType="submit"
                      type="primary"
                      disabled={!dirty || !isValid}
                      loading={isSubmitting}
                      data-testid="save-chat-settings-btn"
                    >
                      Save settings
                    </Button>
                  </Box>

                  <Box
                    borderWidth={1}
                    borderColor="gray.200"
                    borderRadius="md"
                    padding={4}
                    marginTop={4}
                  >
                    <Text fontWeight="semibold" marginBottom={2}>
                      Connection status
                    </Text>
                    {settings?.authorized ? (
                      <>
                        <Text color="green.500" marginBottom={2}>
                          ✓ Authorized
                        </Text>
                        <Button
                          onClick={handleTestConnection}
                          loading={isTesting}
                          disabled={dirty}
                          data-testid="test-chat-connection-btn"
                        >
                          Test connection
                        </Button>
                        {dirty && (
                          <Text fontSize="xs" color="gray.500" marginTop={2}>
                            Save your changes before testing the connection.
                          </Text>
                        )}
                      </>
                    ) : (
                      <>
                        <Text color="orange.500" marginBottom={2}>
                          ⚠ Not authorized
                        </Text>
                        <Button
                          onClick={handleAuthorize}
                          disabled={dirty || !settings?.client_id}
                          data-testid="authorize-chat-btn"
                        >
                          Authorize with Slack
                        </Button>
                        {dirty && (
                          <Text fontSize="xs" color="gray.500" marginTop={2}>
                            Save your settings before authorizing.
                          </Text>
                        )}
                        {!settings?.client_id && !dirty && (
                          <Text fontSize="xs" color="gray.500" marginTop={2}>
                            Enter and save your credentials before authorizing.
                          </Text>
                        )}
                      </>
                    )}
                  </Box>
                </>
              )}
            </Stack>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default ChatProviderSection;
