import {
  Button,
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraStack as Stack,
  ChakraText as Text,
  useChakraToast as useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  ChatProviderConfigCreate,
  ChatProviderConfigUpdate,
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
  useTestChatConnectionMutation,
  useUpdateChatConfigMutation,
} from "./chatProvider.slice";

interface ChatProviderFormValues {
  workspace_url: string;
  client_id: string;
  client_secret: string;
}

const ChatProviderValidationSchema = Yup.object().shape({
  workspace_url: Yup.string().required("Workspace URL is required"),
  client_id: Yup.string(),
  client_secret: Yup.string(),
});

const ChatProviderSection = () => {
  const router = useRouter();
  const toast = useToast();

  // Get config ID from URL if editing
  const configId = useMemo(() => {
    const id = router.query.id;
    return typeof id === "string" ? id : undefined;
  }, [router.query.id]);

  const isEditMode = !!configId;

  // Fetch existing config if editing
  const {
    data: existingConfig,
    isLoading,
    isError,
    refetch,
  } = useGetChatConfigQuery(configId!, { skip: !configId });

  const [createConfig] = useCreateChatConfigMutation();
  const [updateConfig] = useUpdateChatConfigMutation();
  const [testConnection, { isLoading: isTesting }] =
    useTestChatConnectionMutation();
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Check for OAuth callback results in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const chatSuccess = urlParams.get("chat_success");
    const chatError = urlParams.get("chat_error");

    if (chatSuccess === "true") {
      toast(successToastParams("Slack authorization successful!"));
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
      toast(
        errorToastParams(
          errorMessages[chatError] || "Authorization failed. Please try again."
        )
      );
      // Clean up URL but keep id param
      const newUrl = configId
        ? `${window.location.pathname}?id=${configId}`
        : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
  }, [configId, refetch, toast]);

  const initialValues: ChatProviderFormValues = useMemo(
    () => ({
      workspace_url: existingConfig?.workspace_url ?? "",
      client_id: existingConfig?.client_id ?? "",
      client_secret: "",
    }),
    [existingConfig]
  );

  const handleSubmit = async (
    values: ChatProviderFormValues,
    formikHelpers: FormikHelpers<ChatProviderFormValues>
  ) => {
    if (isEditMode && configId) {
      // Update existing config
      const payload: ChatProviderConfigUpdate = {
        workspace_url: values.workspace_url || undefined,
        client_id: values.client_id || undefined,
        client_secret: values.client_secret || undefined,
      };

      const result = await updateConfig({ configId, data: payload });

      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An error occurred while saving."
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Chat provider updated."));
        setHasUnsavedChanges(false);
        formikHelpers.resetForm({
          values: { ...values, client_secret: "" },
        });
        refetch();
      }
    } else {
      // Create new config
      const payload: ChatProviderConfigCreate = {
        provider_type: "slack",
        workspace_url: values.workspace_url,
        client_id: values.client_id || undefined,
        client_secret: values.client_secret || undefined,
      };

      const result = await createConfig(payload);

      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An error occurred while creating."
        );
        toast(errorToastParams(errorMsg));
      } else if ("data" in result && result.data) {
        toast(successToastParams("Chat provider created."));
        // Redirect to edit mode with the new config ID
        router.push(`${CHAT_PROVIDERS_ROUTE}/configure?id=${result.data.id}`);
      }
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
      const errorMsg = getErrorMessage(result.error, "Connection test failed.");
      toast(errorToastParams(errorMsg));
    }
  };

  const handleAuthorize = () => {
    // Open authorization in the same window
    // Include config_id if we're editing
    const authorizeUrl = configId
      ? `/api/v1/plus/chat/authorize?config_id=${configId}`
      : "/api/v1/plus/chat/authorize";
    window.location.href = authorizeUrl;
  };

  const pageTitle = isEditMode ? "Edit Slack integration" : "Add Slack integration";

  if (isLoading && isEditMode) {
    return (
      <Box maxWidth="600px" marginTop="40px">
        <Heading marginBottom={4} fontSize="lg">
          {pageTitle}
        </Heading>
        <Text>Loading...</Text>
      </Box>
    );
  }

  if (isError && isEditMode) {
    return (
      <Box maxWidth="600px" marginTop="40px">
        <Heading marginBottom={4} fontSize="lg">
          {pageTitle}
        </Heading>
        <Text fontSize="sm" color="gray.500">
          Chat provider configuration not found.
        </Text>
      </Box>
    );
  }

  return (
    <Box maxWidth="600px" marginTop="40px">
      <Heading marginBottom={4} fontSize="lg">
        {pageTitle}
      </Heading>
      <Text marginBottom="30px" fontSize="sm">
        Connect your Slack workspace to enable notifications and alerts.
      </Text>

      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={ChatProviderValidationSchema}
      >
        {({ dirty, isValid, isSubmitting }) => (
          <Form data-testid="chat-provider-form">
            <Stack spacing={4}>
              <CustomTextInput
                id="workspace_url"
                name="workspace_url"
                label="Workspace URL"
                placeholder="your-company.slack.com"
                tooltip="Your Slack workspace URL (e.g., your-company.slack.com)"
                variant="stacked"
                isRequired
              />

              <CustomTextInput
                id="client_id"
                name="client_id"
                label="Client ID"
                tooltip="Client ID from your Slack App"
                variant="stacked"
              />

              <CustomTextInput
                id="client_secret"
                name="client_secret"
                label="Client secret"
                type="password"
                tooltip="Client secret from your Slack App (leave blank to keep existing)"
                placeholder={existingConfig?.client_id ? "••••••••" : ""}
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
                  {isEditMode ? "Save changes" : "Create"}
                </Button>
              </Box>

              {isEditMode && existingConfig && (
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
                  {existingConfig.authorized ? (
                    <>
                      <Text color="green.500" marginBottom={2}>
                        Authorized
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
                        Not authorized
                      </Text>
                      <Button
                        onClick={handleAuthorize}
                        disabled={dirty || !existingConfig.client_id}
                        data-testid="authorize-chat-btn"
                      >
                        Authorize with Slack
                      </Button>
                      {dirty && (
                        <Text fontSize="xs" color="gray.500" marginTop={2}>
                          Save your settings before authorizing.
                        </Text>
                      )}
                      {!existingConfig.client_id && !dirty && (
                        <Text fontSize="xs" color="gray.500" marginTop={2}>
                          Enter and save your credentials before authorizing.
                        </Text>
                      )}
                    </>
                  )}
                </Box>
              )}
            </Stack>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default ChatProviderSection;
