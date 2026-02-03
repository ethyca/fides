import {
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraSpinner as Spinner,
  Form,
  Select,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useGetChatSettingsQuery } from "./chatProvider.slice";
import SlackChatProviderForm from "./forms/SlackChatProviderForm";

// Chat provider types
export const chatProviders = {
  slack: "slack",
} as const;

export const chatProviderLabels = {
  slack: "Slack",
} as const;

const ChatProviderConfiguration = () => {
  const [selectedProviderType, setSelectedProviderType] = useState("");

  // Get existing chat provider settings
  const { data: existingSettings, isLoading } = useGetChatSettingsQuery();

  // Check if there's an existing configuration (edit mode)
  const isEditMode = !!existingSettings?.client_id;

  // Auto-select provider if one is already configured
  useEffect(() => {
    if (existingSettings?.provider_type) {
      setSelectedProviderType(existingSettings.provider_type);
    }
  }, [existingSettings?.provider_type]);

  // Provider options for the dropdown
  const providerOptions = useMemo(() => {
    return [
      {
        value: chatProviders.slack,
        label: chatProviderLabels.slack,
        disabled: isEditMode,
        title: isEditMode ? "Slack is already configured" : undefined,
      },
    ];
  }, [isEditMode]);

  // Show loading state
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="200px"
      >
        <Spinner />
      </Box>
    );
  }

  const renderProviderForm = () => {
    switch (selectedProviderType) {
      case chatProviders.slack:
        return <SlackChatProviderForm />;
      default:
        return null;
    }
  };

  return (
    <Box>
      {/* Provider Selection - only show in create mode (when no existing config) */}
      {!isEditMode && (
        <Box
          maxWidth="720px"
          border="1px"
          borderColor="gray.200"
          borderRadius={6}
          overflow="visible"
          mt={6}
          mb={4}
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
            <Heading as="h3" size="xs">
              Select chat provider
            </Heading>
          </Box>
          <Box px={6} py={6}>
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
                  value={selectedProviderType || undefined}
                  onChange={(value) => setSelectedProviderType(value)}
                  options={providerOptions}
                />
              </Form.Item>
            </Form>
          </Box>
        </Box>
      )}

      {/* Render the appropriate form based on selected provider */}
      {selectedProviderType && renderProviderForm()}
    </Box>
  );
};

export default ChatProviderConfiguration;
