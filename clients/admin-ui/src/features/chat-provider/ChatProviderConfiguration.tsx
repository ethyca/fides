import { Flex, Form, Select, Spin, Typography } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { useGetChatConfigQuery } from "./chatProvider.slice";
import SlackChatProviderForm from "./forms/SlackChatProviderForm";

const { Title } = Typography;

// Chat provider types
export const chatProviders = {
  slack: "slack",
} as const;

export const chatProviderLabels = {
  slack: "Slack",
} as const;

const ChatProviderConfiguration = () => {
  const router = useRouter();
  const [selectedProviderType, setSelectedProviderType] = useState("");

  // Get config ID from URL if editing
  const configId = useMemo(() => {
    const { id } = router.query;
    return typeof id === "string" ? id : undefined;
  }, [router.query]);

  // Check if we're in edit mode based on URL parameter
  const isEditMode = !!configId;

  // Fetch existing config if editing
  const { data: existingConfig, isLoading } = useGetChatConfigQuery(configId!, {
    skip: !configId,
  });

  // Auto-select provider if one is already configured (edit mode)
  useEffect(() => {
    if (existingConfig?.provider_type) {
      setSelectedProviderType(existingConfig.provider_type);
    }
  }, [existingConfig?.provider_type]);

  // Provider options for the dropdown
  const providerOptions = useMemo(() => {
    return [
      {
        value: chatProviders.slack,
        label: chatProviderLabels.slack,
      },
    ];
  }, []);

  // Show loading state
  if (isLoading) {
    return (
      <Flex justify="center" align="center" style={{ height: "200px" }}>
        <Spin size="large" />
      </Flex>
    );
  }

  const renderProviderForm = () => {
    switch (selectedProviderType) {
      case chatProviders.slack:
        return <SlackChatProviderForm configId={configId} />;
      default:
        return null;
    }
  };

  return (
    <div>
      {/* Provider Selection - only show in create mode (when no existing config) */}
      {!isEditMode && (
        <div
          className="mb-4 mt-6"
          style={{
            maxWidth: "720px",
            border: "1px solid #e5e7eb",
            borderRadius: 6,
            overflow: "visible",
          }}
        >
          <Flex
            align="center"
            style={{
              backgroundColor: "#f9fafb",
              padding: "16px 24px",
              borderBottom: "1px solid #e5e7eb",
              borderTopLeftRadius: 6,
              borderTopRightRadius: 6,
            }}
          >
            <Title level={5} style={{ margin: 0 }}>
              Select chat provider
            </Title>
          </Flex>
          <div style={{ padding: "24px" }}>
            <Form layout="vertical">
              <Form.Item
                label="Provider type"
                name="provider_type"
                rules={[
                  { required: true, message: "Please select a provider type" },
                ]}
              >
                <Select
                  placeholder="Choose a chat provider..."
                  aria-label="Select a chat provider"
                  data-testid="chat-provider-type-select"
                  value={selectedProviderType ?? undefined}
                  onChange={(value) => setSelectedProviderType(value)}
                  options={providerOptions}
                />
              </Form.Item>
            </Form>
          </div>
        </div>
      )}

      {/* Render the appropriate form based on selected provider */}
      {selectedProviderType && renderProviderForm()}
    </div>
  );
};

export default ChatProviderConfiguration;
