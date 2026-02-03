import { Button, Flex, Form, Input, Space, useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import {
  ChatConfigCreate,
  ChatConfigUpdate,
} from "~/types/api";

import {
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
  useUpdateChatConfigMutation,
} from "../chatProvider.slice";
import AuthorizationStatus from "../components/AuthorizationStatus";
import ConfigurationCard from "../components/ConfigurationCard";
import { SECRET_PLACEHOLDER } from "../constants";
import SlackIcon from "../icons/SlackIcon";
import { cleanupUrlParams, getOAuthErrorMessage } from "../utils/urlHelpers";

interface SlackChatFormProps {
  configId?: string;
}

const SlackChatForm = ({ configId }: SlackChatFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const message = useMessage();
  const [form] = Form.useForm();

  // Watch any form field change to trigger re-render for button state
  Form.useWatch([], form);

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
      cleanupUrlParams(configId ? { id: configId } : undefined);
    } else if (chatError) {
      message.error(getOAuthErrorMessage(chatError));
      cleanupUrlParams(configId ? { id: configId } : undefined);
    }
  }, [refetch, message, configId]);

  const hasSigningSecret = existingConfig?.has_signing_secret;

  const initialValues = {
    workspace_url: existingConfig?.workspace_url ?? "",
    client_id: existingConfig?.client_id ?? "",
    client_secret: isEditMode ? SECRET_PLACEHOLDER : "",
    signing_secret: isEditMode && hasSigningSecret ? SECRET_PLACEHOLDER : "",
  };

  // Update form when existingConfig changes
  useEffect(() => {
    if (existingConfig) {
      form.setFieldsValue({
        workspace_url: existingConfig.workspace_url ?? "",
        client_id: existingConfig.client_id ?? "",
        client_secret: SECRET_PLACEHOLDER,
        signing_secret: existingConfig.has_signing_secret
          ? SECRET_PLACEHOLDER
          : "",
      });
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
        const payload: ChatConfigUpdate = {
          workspace_url: values.workspace_url || undefined,
          client_id: values.client_id || undefined,
          // Only send secrets if they're not the placeholder
          client_secret:
            values.client_secret && values.client_secret !== SECRET_PLACEHOLDER
              ? values.client_secret
              : undefined,
          signing_secret:
            values.signing_secret &&
            values.signing_secret !== SECRET_PLACEHOLDER
              ? values.signing_secret
              : undefined,
        };

        const result = await updateConfig({ configId, data: payload });

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          message.success("Slack configuration saved successfully.");
          refetch();
          // Reset form with current values but clear the secrets
          form.setFieldsValue({
            ...values,
            client_secret: SECRET_PLACEHOLDER,
            signing_secret: values.signing_secret ? SECRET_PLACEHOLDER : "",
          });
        }
      } else {
        // Create new config
        const payload: ChatConfigCreate = {
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

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleSubmit}
    >
      <ConfigurationCard
        title="Slack chat provider configuration"
        icon={<SlackIcon />}
      >
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
        >
          <Input
            placeholder="your-company.slack.com"
            data-testid="workspace-url-input"
          />
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
        >
          <Input
            placeholder="Enter your Slack App Client ID"
            data-testid="client-id-input"
          />
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
        >
          <Input.Password
            placeholder={
              isEditMode
                ? "Enter new client secret to change"
                : "Enter your Slack App Client Secret"
            }
            data-testid="client-secret-input"
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
            data-testid="signing-secret-input"
          />
        </Form.Item>

        <Flex justify="flex-end" className="mt-6">
          <Space>
            {isEditMode ? (
              <>
                {/* Authorize button - show when not authorized */}
                {!isAuthorized && (
                  <Button
                    onClick={handleAuthorize}
                    disabled={form.isFieldsTouched()}
                    data-testid="authorize-chat-btn"
                  >
                    Authorize with Slack
                  </Button>
                )}
                {/* Authorized status - show when OAuth is complete */}
                {isAuthorized && <AuthorizationStatus authorized />}
              </>
            ) : (
              <Button
                onClick={() => router.push(CHAT_PROVIDERS_ROUTE)}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
            )}
            <Button
              htmlType="submit"
              type="primary"
              data-testid="save-btn"
              disabled={!form.isFieldsTouched()}
            >
              Save
            </Button>
          </Space>
        </Flex>
      </ConfigurationCard>
    </Form>
  );
};

export default SlackChatForm;
