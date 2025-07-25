import { Box, Heading, Spinner, Text } from "fidesui";
import { useEffect } from "react";

import { useAPIHelper } from "~/features/common/hooks";

import { messagingProviders } from "./constants";
import { useGetMessagingConfigurationByKeyQuery } from "./messaging.slice";
import MessagingConfiguration from "./MessagingConfiguration";

interface EditMessagingConfigurationProps {
  configKey: string;
}

export const EditMessagingConfiguration = ({
  configKey,
}: EditMessagingConfigurationProps) => {
  const { handleError } = useAPIHelper();

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
      <Box>
        <Text color="red.500">
          Messaging configuration not found for key: {configKey}
        </Text>
      </Box>
    );
  }

  const serviceType = messagingConfig.service_type;

  return (
    <Box>
      <Heading fontSize="2xl" fontWeight="semibold">
        Edit messaging provider
      </Heading>

      <Box display="flex" flexDirection="column" width="50%">
        {Object.values(messagingProviders).includes(serviceType) ? (
          <MessagingConfiguration
            configKey={configKey}
            initialProviderType={serviceType}
          />
        ) : (
          <Text color="red.500">Unsupported service type: {serviceType}</Text>
        )}
      </Box>
    </Box>
  );
};
