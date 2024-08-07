import { Box, Button, ButtonGroup, Flex, Text, Wrap } from "fidesui";
import { ReactNode } from "react";

import Tag from "~/features/common/Tag";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const IntegrationBox = ({
  integration,
  showTestNotice,
  otherButtons,
  configureButtonLabel = "Configure",
  onConfigureClick,
}: {
  integration?: ConnectionConfigurationResponse;
  showTestNotice?: boolean;
  otherButtons?: ReactNode;
  configureButtonLabel?: string;
  onConfigureClick?: () => void;
}) => {
  const { testConnection, isLoading, testData } =
    useTestConnection(integration);

  const integrationTypeInfo = getIntegrationTypeInfo(
    integration?.connection_type,
  );

  return (
    <Box
      maxW="760px"
      borderWidth={1}
      borderRadius="lg"
      overflow="hidden"
      padding="12px"
      marginBottom="24px"
      data-testid={`integration-info-${integration?.key}`}
    >
      <Flex>
        <ConnectionTypeLogo data={integration ?? ""} boxSize="50px" />
        <Flex direction="column" flexGrow={1} marginLeft="16px">
          <Text color="gray.700" fontWeight="semibold">
            {integration?.name || "(No name)"}
          </Text>
          {showTestNotice ? (
            <ConnectionStatusNotice testData={testData} />
          ) : (
            <Text color="gray.700" fontSize="sm" fontWeight="semibold" mt={1}>
              {integrationTypeInfo.category}
            </Text>
          )}
        </Flex>
        <ButtonGroup size="sm" variant="outline">
          {showTestNotice && (
            <Button
              onClick={testConnection}
              isLoading={isLoading}
              data-testid="test-connection-btn"
            >
              Test connection
            </Button>
          )}
          {otherButtons}
          {onConfigureClick && (
            <Button onClick={onConfigureClick} data-testid="configure-btn">
              {configureButtonLabel}
            </Button>
          )}
        </ButtonGroup>
      </Flex>
      <Wrap marginTop="16px">
        {integrationTypeInfo.tags.map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
      </Wrap>
    </Box>
  );
};

export default IntegrationBox;
