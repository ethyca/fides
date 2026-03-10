import { Flex, Form, Select, Spin } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { useGetChatConfigQuery } from "./chatProvider.slice";
import ConfigurationCard from "./components/ConfigurationCard";
import { CHAT_PROVIDER_LABELS, CHAT_PROVIDER_TYPES } from "./constants";
import SlackChatForm from "./forms/SlackChatForm";

const ChatConfiguration = () => {
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
        value: CHAT_PROVIDER_TYPES.SLACK,
        label: CHAT_PROVIDER_LABELS[CHAT_PROVIDER_TYPES.SLACK],
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
      case CHAT_PROVIDER_TYPES.SLACK:
        return <SlackChatForm configId={configId} />;
      default:
        return null;
    }
  };

  return (
    <div>
      {/* Provider Selection - only show in create mode (when no existing config) */}
      {!isEditMode && (
        <ConfigurationCard title="Select chat provider">
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
        </ConfigurationCard>
      )}

      {/* Render the appropriate form based on selected provider */}
      {selectedProviderType && renderProviderForm()}
    </div>
  );
};

export default ChatConfiguration;
