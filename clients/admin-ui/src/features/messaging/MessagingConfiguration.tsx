import { Box, Heading, Spinner, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useEffect, useState } from "react";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { useAPIHelper } from "~/features/common/hooks";

import { messagingProviderLabels, messagingProviders } from "./constants";
import MailgunMessagingForm from "./MailgunMessagingForm";
import { useGetMessagingConfigurationByKeyQuery } from "./messaging.slice";
import TwilioEmailMessagingForm from "./TwilioEmailMessagingForm";
import TwilioSMSMessagingForm from "./TwilioSMSMessagingForm";

interface MessagingConfigurationProps {
  configKey?: string; // If provided, we're in edit mode
  initialProviderType?: string; // Allow setting initial provider type
}

const MessagingConfiguration = ({
  configKey,
  initialProviderType = messagingProviders.mailgun,
}: MessagingConfigurationProps) => {
  const [selectedProviderType, setSelectedProviderType] =
    useState(initialProviderType);

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

  // Provider options for the dropdown
  const providerOptions = [
    {
      value: messagingProviders.mailgun,
      label: messagingProviderLabels.mailgun,
    },
    {
      value: messagingProviders.twilio_email,
      label: messagingProviderLabels.twilio_email,
    },
    {
      value: messagingProviders.twilio_text,
      label: messagingProviderLabels.twilio_text,
    },
  ];

  const renderProviderForm = () => {
    switch (selectedProviderType) {
      case messagingProviders.mailgun:
        return <MailgunMessagingForm configKey={configKey} />;
      case messagingProviders.twilio_email:
        return <TwilioEmailMessagingForm configKey={configKey} />;
      case messagingProviders.twilio_text:
        return <TwilioSMSMessagingForm configKey={configKey} />;
      default:
        return <TwilioSMSMessagingForm configKey={configKey} />;
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
            <Formik
              initialValues={{ provider_type: selectedProviderType }}
              onSubmit={() => {}}
              enableReinitialize
            >
              <Form>
                <ControlledSelect
                  name="provider_type"
                  label="Provider type"
                  options={providerOptions}
                  layout="stacked"
                  isRequired
                  value={selectedProviderType}
                  onChange={(value) => setSelectedProviderType(value)}
                />
              </Form>
            </Formik>
          </Box>
        </Box>
      )}

      {/* Render the appropriate form based on selected provider */}
      {renderProviderForm()}
    </Box>
  );
};

export default MessagingConfiguration;
