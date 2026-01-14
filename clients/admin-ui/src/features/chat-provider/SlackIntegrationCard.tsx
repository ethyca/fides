import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  useChakraToast as useToast,
} from "fidesui";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  useDeleteChatConnectionMutation,
  useGetChatChannelsQuery,
  useGetChatSettingsQuery,
  useGetQuestionsQuery,
  usePostQuestionsMutation,
  useSendChatMessageMutation,
  useTestChatConnectionMutation,
  useUpdateChatSettingsMutation,
} from "./chatProvider.slice";
import styles from "./SlackIntegrationCard.module.scss";

const { Text, Title, Paragraph } = Typography;

const SlackLogo = () => (
  <svg
    width="32"
    height="32"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z"
      fill="#E01E5A"
    />
    <path
      d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z"
      fill="#36C5F0"
    />
    <path
      d="M18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zm-1.27 0a2.528 2.528 0 0 1-2.522 2.521 2.528 2.528 0 0 1-2.52-2.521V2.522A2.528 2.528 0 0 1 15.165 0a2.528 2.528 0 0 1 2.521 2.522v6.312z"
      fill="#2EB67D"
    />
    <path
      d="M15.165 18.956a2.528 2.528 0 0 1 2.521 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zm0-1.27a2.527 2.527 0 0 1-2.52-2.522 2.527 2.527 0 0 1 2.52-2.52h6.313A2.528 2.528 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.521h-6.313z"
      fill="#ECB22E"
    />
  </svg>
);

const SlackIntegrationCard = () => {
  const toast = useToast();
  const {
    data: settings,
    isLoading,
    isError,
    refetch,
  } = useGetChatSettingsQuery();
  const [updateSettings, { isLoading: isSaving }] =
    useUpdateChatSettingsMutation();
  const [testConnection, { isLoading: isTesting }] =
    useTestChatConnectionMutation();
  const [deleteConnection, { isLoading: isDeleting }] =
    useDeleteChatConnectionMutation();
  const [sendMessage, { isLoading: isSending }] = useSendChatMessageMutation();
  const [postQuestions, { isLoading: isPostingQuestions }] =
    usePostQuestionsMutation();

  // Track if there's an active conversation for polling speed
  const [hasActiveConversation, setHasActiveConversation] = useState(false);

  // Poll faster (3s) when a conversation is active, slower (30s) otherwise
  const pollingInterval = hasActiveConversation ? 3000 : 30000;

  const { data: questionsData, refetch: refetchQuestions } =
    useGetQuestionsQuery(undefined, {
      skip: !settings?.authorized,
      pollingInterval,
    });

  // Update active conversation state when data changes
  useEffect(() => {
    const isActive = questionsData?.conversations?.some(
      (conv) => conv.status === "in_progress"
    );
    setHasActiveConversation(isActive ?? false);
  }, [questionsData?.conversations]);

  const { data: channelsData } = useGetChatChannelsQuery(undefined, {
    skip: !settings?.authorized,
  });

  const [selectedChannel, setSelectedChannel] = useState<string | undefined>(
    undefined
  );
  const [testMessage, setTestMessage] = useState<string>(
    "Hello from Fides! This is a test message."
  );

  // Credentials form state
  const [clientId, setClientId] = useState<string>("");
  const [clientSecret, setClientSecret] = useState<string>("");
  const [signingSecret, setSigningSecret] = useState<string>("");

  // Update selected channel when settings load
  useEffect(() => {
    if (settings?.notification_channel_id) {
      setSelectedChannel(settings.notification_channel_id);
    }
  }, [settings?.notification_channel_id]);

  // Handle OAuth callback results
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const chatSuccess = urlParams.get("chat_success");
    const chatError = urlParams.get("chat_error");

    if (chatSuccess === "true") {
      toast(successToastParams("Slack connected successfully!"));
      refetch();
      window.history.replaceState({}, "", window.location.pathname);
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
          errorMessages[chatError] ?? "Authorization failed. Please try again."
        )
      );
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [refetch, toast]);

  // Update form state when settings load (for editing existing credentials)
  useEffect(() => {
    if (settings?.client_id) {
      setClientId(settings.client_id);
    }
  }, [settings?.client_id]);

  const handleSaveCredentials = async () => {
    if (!clientId.trim() || !clientSecret.trim()) {
      toast(errorToastParams("Client ID and Client Secret are required."));
      return;
    }

    const result = await updateSettings({
      enabled: true,
      provider_type: "slack",
      client_id: clientId.trim(),
      client_secret: clientSecret.trim(),
      signing_secret: signingSecret.trim() || undefined,
    });

    if (isErrorResult(result)) {
      toast(
        errorToastParams(getErrorMessage(result.error, "Failed to save credentials."))
      );
    } else {
      toast(successToastParams("Credentials saved. You can now connect to Slack."));
      setClientSecret(""); // Clear secrets after save
      setSigningSecret("");
      refetch();
    }
  };

  const handleConnect = () => {
    window.location.href = "/api/v1/plus/chat/authorize";
  };

  const hasCredentials = Boolean(settings?.client_id);

  const handleTestConnection = async () => {
    const result = await testConnection();

    if ("data" in result && result.data) {
      if (result.data.success) {
        toast(successToastParams(result.data.message));
      } else {
        toast(errorToastParams(result.data.message));
      }
    } else if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error, "Test failed.")));
    }
  };

  const handleDisconnect = async () => {
    const result = await deleteConnection();

    if (isErrorResult(result)) {
      toast(
        errorToastParams(getErrorMessage(result.error, "Disconnect failed."))
      );
    } else {
      toast(successToastParams("Slack disconnected successfully."));
      refetch();
    }
  };

  const handleChannelChange = async (value: string) => {
    setSelectedChannel(value);

    const result = await updateSettings({
      enabled: true,
      provider_type: "slack",
      notification_channel_id: value,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error, "Save failed.")));
    } else {
      toast(successToastParams("Channel updated."));
    }
  };

  const handleSendMessage = async () => {
    if (!selectedChannel || !testMessage.trim()) {
      toast(errorToastParams("Please select a channel and enter a message."));
      return;
    }

    const result = await sendMessage({
      channel_id: selectedChannel,
      message: testMessage,
    });

    if ("data" in result && result.data) {
      if (result.data.success) {
        toast(successToastParams(result.data.message));
      } else {
        toast(errorToastParams(result.data.message));
      }
    } else if (isErrorResult(result)) {
      toast(
        errorToastParams(getErrorMessage(result.error, "Failed to send message."))
      );
    }
  };

  const handlePostQuestions = async () => {
    const result = await postQuestions();

    if ("data" in result && result.data) {
      if (result.data.success) {
        toast(successToastParams(result.data.message));
        refetchQuestions();
      } else {
        toast(errorToastParams(result.data.message));
      }
    } else if (isErrorResult(result)) {
      toast(
        errorToastParams(
          getErrorMessage(result.error, "Failed to post questions.")
        )
      );
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <Card className={styles.card}>
        <Flex align="center" gap={12}>
          <SlackLogo />
          <Title level={5} className="m-0">
            Slack
          </Title>
        </Flex>
        <Paragraph className={styles.description}>Loading...</Paragraph>
      </Card>
    );
  }

  // Not connected state
  if (!settings?.authorized || isError) {
    return (
      <Card className={styles.card} data-testid="slack-integration-card">
        <div className={styles.header}>
          <Flex align="center" gap={12}>
            <SlackLogo />
            <Title level={5} className="m-0">
              Slack
            </Title>
          </Flex>
        </div>

        <Paragraph className={styles.description}>
          Receive AI-powered privacy insights and alerts directly in your Slack
          workspace.
        </Paragraph>

        <Flex align="center" gap={8} className="mb-4">
          <Text strong>Status:</Text>
          <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Not connected</Tag>
        </Flex>

        <Space direction="vertical" size={12} className="w-full mb-4">
          <div>
            <Text strong className="mb-1 block">
              Slack app credentials
            </Text>
            <Text type="secondary" className="mb-3 block">
              Create a Slack app at{" "}
              <a
                href="https://api.slack.com/apps"
                target="_blank"
                rel="noopener noreferrer"
              >
                api.slack.com/apps
              </a>{" "}
              and enter your app credentials below.
            </Text>
          </div>

          <div>
            <Text className="mb-1 block">Client ID</Text>
            <Input
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Enter Slack app Client ID"
              data-testid="slack-client-id-input"
            />
          </div>

          <div>
            <Text className="mb-1 block">Client Secret</Text>
            <Input.Password
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder={
                hasCredentials
                  ? "Enter new secret to update"
                  : "Enter Slack app Client Secret"
              }
              data-testid="slack-client-secret-input"
            />
          </div>

          <div>
            <Text className="mb-1 block">
              Signing Secret{" "}
              <Text type="secondary">(optional, for webhooks)</Text>
            </Text>
            <Input.Password
              value={signingSecret}
              onChange={(e) => setSigningSecret(e.target.value)}
              placeholder={
                settings?.has_signing_secret
                  ? "Enter new secret to update"
                  : "Enter Slack app Signing Secret"
              }
              data-testid="slack-signing-secret-input"
            />
          </div>

          <Flex gap={8}>
            <Button
              onClick={handleSaveCredentials}
              loading={isSaving}
              disabled={!clientId.trim() || !clientSecret.trim()}
              data-testid="save-slack-credentials-btn"
            >
              Save credentials
            </Button>

            <Button
              type="primary"
              onClick={handleConnect}
              disabled={!hasCredentials}
              data-testid="connect-slack-btn"
            >
              Connect to Slack
            </Button>
          </Flex>

          {!hasCredentials && (
            <Text type="secondary">
              Save your credentials first, then click &quot;Connect to
              Slack&quot; to authorize.
            </Text>
          )}
        </Space>
      </Card>
    );
  }

  // Connected state
  return (
    <Card className={styles.card} data-testid="slack-integration-card">
      <div className={styles.header}>
        <Flex align="center" gap={12}>
          <SlackLogo />
          <Title level={5} className="m-0">
            Slack
          </Title>
        </Flex>
        <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Connected</Tag>
      </div>

      <Space direction="vertical" size={4} className="mb-4">
        {settings.workspace_name && (
          <Text>
            <Text strong>Workspace:</Text> {settings.workspace_name}
          </Text>
        )}
        {settings.connected_by_email && (
          <Text>
            <Text strong>Connected by:</Text> {settings.connected_by_email}
          </Text>
        )}
        {settings.created_at && (
          <Text>
            <Text strong>Connected on:</Text> {formatDate(settings.created_at)}
          </Text>
        )}
      </Space>

      <div className={styles.channelSection}>
        <Text strong className="mb-2 block">
          Notification settings
        </Text>
        <Flex align="center" gap={8}>
          <Text>Channel for AI insights:</Text>
          <Select
            value={selectedChannel}
            onChange={handleChannelChange}
            placeholder="Select a channel"
            className={styles.channelSelect}
            options={channelsData?.channels?.map((channel) => ({
              value: channel.id,
              label: `#${channel.name}`,
            }))}
            loading={!channelsData}
            data-testid="slack-channel-select"
          />
        </Flex>
      </div>

      <div className={styles.testMessageSection}>
        <Text strong className="mb-2 block">
          Send test message
        </Text>
        <Flex gap={8}>
          <Input
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter a test message..."
            className={styles.messageInput}
            data-testid="slack-test-message-input"
          />
          <Button
            onClick={handleSendMessage}
            loading={isSending}
            disabled={!selectedChannel}
            data-testid="send-slack-message-btn"
          >
            Send
          </Button>
        </Flex>
        {!selectedChannel && (
          <Text type="secondary" className="mt-1 block">
            Select a channel first to send a test message.
          </Text>
        )}
      </div>

      <Flex gap={8} className="mt-4">
        <Button
          onClick={handleTestConnection}
          loading={isTesting}
          data-testid="test-slack-btn"
        >
          Test connection
        </Button>
        <Button
          danger
          onClick={handleDisconnect}
          loading={isDeleting}
          data-testid="disconnect-slack-btn"
        >
          Disconnect
        </Button>
      </Flex>

      {/* Conversational Q&A Section */}
      <div className={styles.qaSection}>
        <Flex justify="space-between" align="center" className="mb-3">
          <Text strong>Team Q&A Conversations</Text>
          <Flex gap={8}>
            <Button
              onClick={() => refetchQuestions()}
              size="small"
              data-testid="refresh-questions-btn"
            >
              Refresh
            </Button>
            <Button
              type="primary"
              onClick={handlePostQuestions}
              loading={isPostingQuestions}
              disabled={!selectedChannel}
              size="small"
              data-testid="post-questions-btn"
            >
              Start conversation
            </Button>
          </Flex>
        </Flex>

        {!selectedChannel && (
          <Text type="secondary" className="mb-3 block">
            Select a channel above to start a conversation.
          </Text>
        )}

        {questionsData?.conversations &&
        questionsData.conversations.length > 0 ? (
          <Space direction="vertical" size={12} className="w-full">
            {questionsData.conversations.map((conv) => {
              const answeredCount = conv.questions.filter(
                (q) => q.answer !== null
              ).length;
              const totalQuestions = conv.questions.length;
              const isCompleted = conv.status === "completed";

              return (
                <Card
                  key={conv.thread_ts}
                  size="small"
                  className={styles.questionCard}
                >
                  <Flex justify="space-between" align="center" className="mb-2">
                    <Text strong>
                      Conversation started {formatDateTime(conv.created_at)}
                    </Text>
                    <Tag
                      color={
                        isCompleted
                          ? CUSTOM_TAG_COLOR.SUCCESS
                          : CUSTOM_TAG_COLOR.PROCESSING
                      }
                    >
                      {isCompleted
                        ? "Completed"
                        : `${answeredCount}/${totalQuestions} answered`}
                    </Tag>
                  </Flex>

                  <div className={styles.answersContainer}>
                    {conv.questions.map((q, idx) => (
                      <div key={idx} className={styles.qaItem}>
                        <Text strong className="block">
                          Q{idx + 1}: {q.question}
                        </Text>
                        {q.answer ? (
                          <Text className="block ml-4">
                            <Text type="secondary">A:</Text> {q.answer}
                            {(q.user_email ?? q.user) && (
                              <Text type="secondary">
                                {" "}
                                (by {q.user_email ?? q.user})
                              </Text>
                            )}
                          </Text>
                        ) : idx === conv.current_question_index &&
                          !isCompleted ? (
                          <Text type="secondary" italic className="block ml-4">
                            Waiting for answer...
                          </Text>
                        ) : (
                          <Text type="secondary" className="block ml-4">
                            —
                          </Text>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              );
            })}
          </Space>
        ) : (
          <Text type="secondary">
            No conversations yet. Click &quot;Start conversation&quot; to begin
            asking fun questions to your team!
          </Text>
        )}
      </div>
    </Card>
  );
};

export default SlackIntegrationCard;
