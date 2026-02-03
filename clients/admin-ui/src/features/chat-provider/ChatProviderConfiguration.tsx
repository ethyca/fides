import {
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraSpinner as Spinner,
  Form,
  Select,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { useGetChatConfigQuery } from "./chatProvider.slice";
import SlackChatProviderForm from "./forms/SlackChatProviderForm";

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
    const id = router.query.id;
    return typeof id === "string" ? id : undefined;
  }, [router.query.id]);

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
        return <SlackChatProviderForm configId={configId} />;
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
