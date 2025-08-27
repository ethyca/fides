import {
  AntForm as Form,
  AntSelect as Select,
  Box,
  Heading,
  Spinner,
  Text,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useAPIHelper } from "~/features/common/hooks";

import AwsSesMessagingForm from "./AwsSesMessagingForm";
import { messagingProviderLabels, messagingProviders } from "./constants";
import MailgunMessagingForm from "./MailgunMessagingForm";
import {
  useGetMessagingConfigurationByKeyQuery,
  useGetMessagingConfigurationsQuery,
} from "./messaging.slice";
import TwilioEmailMessagingForm from "./TwilioEmailMessagingForm";
import TwilioSMSMessagingForm from "./TwilioSMSMessagingForm";

interface MessagingConfigurationProps {
  configKey?: string; // If provided, we're in edit mode
  initialProviderType?: string; // Allow setting initial provider type
}

const MessagingConfiguration = ({
  configKey,
  initialProviderType,
}: MessagingConfigurationProps) => {
  const [selectedProviderType, setSelectedProviderType] = useState(
    initialProviderType || "",
  );

  const isEditMode = !!configKey;
  const { handleError } = useAPIHelper();

  // For editing: fetch existing config by key
  const {
    data: messagingConfig,
    isLoading,
    error,
  } = useGetMessagingConfigurationByKeyQuery(
    { key: configKey! },
    { skip: !configKey },
  );

  // Get existing configurations to determine which types are already in use
  const { data: existingConfigurations } = useGetMessagingConfigurationsQuery();

  // Update selected provider type when config is loaded in edit mode
  useEffect(() => {
    if (isEditMode && messagingConfig?.service_type) {
      setSelectedProviderType(messagingConfig.service_type);
    }
  }, [isEditMode, messagingConfig?.service_type]);

  useEffect(() => {
    if (error) {
      handleError(error);
    }
  }, [error, handleError]);

  // Provider options for the dropdown
  const providerOptions = useMemo(() => {
    const usedServiceTypes = new Set(
      existingConfigurations?.items?.map((config) => config.service_type) || [],
    );

    const isMailgunUsed =
      !isEditMode && usedServiceTypes.has(messagingProviders.mailgun as any);
    const isTwilioEmailUsed =
      !isEditMode &&
      usedServiceTypes.has(messagingProviders.twilio_email as any);
    const isTwilioTextUsed =
      !isEditMode &&
      usedServiceTypes.has(messagingProviders.twilio_text as any);
    const isAwsSesUsed =
      !isEditMode && usedServiceTypes.has(messagingProviders.aws_ses as any);

    return [
      {
        value: messagingProviders.mailgun,
        label: messagingProviderLabels.mailgun,
        disabled: isMailgunUsed,
        title: isMailgunUsed
          ? "Only one messaging provider of each type can be created"
          : undefined,
      },
      {
        value: messagingProviders.twilio_email,
        label: messagingProviderLabels.twilio_email,
        disabled: isTwilioEmailUsed,
        title: isTwilioEmailUsed
          ? "Only one messaging provider of each type can be created"
          : undefined,
      },
      {
        value: messagingProviders.twilio_text,
        label: messagingProviderLabels.twilio_text,
        disabled: isTwilioTextUsed,
        title: isTwilioTextUsed
          ? "Only one messaging provider of each type can be created"
          : undefined,
      },
      {
        value: messagingProviders.aws_ses,
        label: messagingProviderLabels.aws_ses,
        disabled: isAwsSesUsed,
        title: isAwsSesUsed
          ? "Only one messaging provider of each type can be created"
          : undefined,
      },
    ];
  }, [existingConfigurations, isEditMode]);

  // Show loading state in edit mode
  if (isEditMode && isLoading) {
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

  // Show error state in edit mode
  if (isEditMode && !messagingConfig && !isLoading) {
    return (
      <Box>
        <Text color="red.500">
          Messaging configuration not found for key: {configKey}
        </Text>
      </Box>
    );
  }

  const renderProviderForm = () => {
    switch (selectedProviderType) {
      case messagingProviders.mailgun:
        return <MailgunMessagingForm configKey={configKey} />;
      case messagingProviders.twilio_email:
        return <TwilioEmailMessagingForm configKey={configKey} />;
      case messagingProviders.twilio_text:
        return <TwilioSMSMessagingForm configKey={configKey} />;
      case messagingProviders.aws_ses:
        return <AwsSesMessagingForm configKey={configKey} />;
      default:
        return null;
    }
  };

  return (
    <Box>
      {/* Provider Selection - only show in create mode */}
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
              Select messaging provider
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
                  placeholder="Choose a messaging provider..."
                  value={selectedProviderType || undefined}
                  onChange={(value) => setSelectedProviderType(value)}
                  options={providerOptions}
                />
              </Form.Item>
            </Form>
          </Box>
        </Box>
      )}

      {/* Render the appropriate form based on selected provider - only if a provider is selected */}
      {selectedProviderType && renderProviderForm()}
    </Box>
  );
};

export default MessagingConfiguration;
