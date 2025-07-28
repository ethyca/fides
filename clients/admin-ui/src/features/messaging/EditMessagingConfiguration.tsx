import { AntCard as Card, Box, Heading, Spinner, Text } from "fidesui";
import { useEffect, useState } from "react";

import { useAPIHelper } from "~/features/common/hooks";

import { messagingProviders } from "./constants";
import { useGetMessagingConfigurationByKeyQuery } from "./messaging.slice";
import MessagingConfiguration from "./MessagingConfiguration";
import { TestMessagingProviderModal } from "./TestMessagingProviderModal";

interface EditMessagingConfigurationProps {
  configKey: string;
}

export const EditMessagingConfiguration = ({
  configKey,
}: EditMessagingConfigurationProps) => {
  const { handleError } = useAPIHelper();
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);

  const {
    data: messagingConfig,
    isLoading,
    error,
  } = useGetMessagingConfigurationByKeyQuery({ key: configKey });

  useEffect(() => {
    if (error) {
      handleError(error);
    }
  }, [error, handleError]);

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

  if (!messagingConfig) {
    return (
      <Card>
        <Text color="red.500">
          Messaging configuration not found for key: {configKey}
        </Text>
      </Card>
    );
  }

  const serviceType = messagingConfig.service_type;

  return (
    <Box>
      <Heading fontSize="2xl" fontWeight="semibold" mb={6}>
        Edit messaging provider
      </Heading>

      {Object.values(messagingProviders).includes(serviceType) ? (
        <MessagingConfiguration
          configKey={configKey}
          initialProviderType={serviceType}
        />
      ) : (
        <Text color="red.500">Unsupported service type: {serviceType}</Text>
      )}

      <TestMessagingProviderModal
        serviceType={messagingConfig?.service_type}
        isOpen={isTestModalOpen}
        onClose={() => setIsTestModalOpen(false)}
      />
    </Box>
  );
};
