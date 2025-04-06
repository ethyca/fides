import {
  AntButton as Button,
  AntTag as Tag,
  Box,
  Flex,
  Text,
  Wrap,
} from "fidesui";
import { ReactNode } from "react";

import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import DeleteConnectionModal from "~/features/datastore-connections/DeleteConnectionModal";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const IntegrationBox = ({
  integration,
  showTestNotice,
  otherButtons,
  showDeleteButton,
  configureButtonLabel = "Configure",
  onConfigureClick,
}: {
  integration?: ConnectionConfigurationResponse;
  showTestNotice?: boolean;
  otherButtons?: ReactNode;
  showDeleteButton?: boolean;
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
        <div className="flex gap-4">
          {showDeleteButton && integration && (
            <DeleteConnectionModal
              showMenu={false}
              connection_key={integration.key}
            />
          )}
          {showTestNotice && (
            <Button
              onClick={testConnection}
              loading={isLoading}
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
        </div>
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
