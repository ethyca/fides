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
import { useIntegrationAuthorization } from "~/features/integrations/hooks/useIntegrationAuthorization";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
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
    integration?.saas_config?.type,
  );

  // Only pass the saas type if it's a valid SaasConnectionTypes value
  const saasType = integration?.saas_config?.type;
  const isSaasType = (type: string): type is SaasConnectionTypes =>
    Object.values(SaasConnectionTypes).includes(type as SaasConnectionTypes);

  const connectionOption = useIntegrationOption(
    integration?.connection_type,
    saasType && isSaasType(saasType) ? saasType : undefined,
  );

  const { handleAuthorize, needsAuthorization } = useIntegrationAuthorization({
    connection: integration,
    connectionOption,
    testData,
  });

  return (
    <Box
      borderWidth={1}
      borderColor="gray.200"
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
            <ConnectionStatusNotice
              testData={testData}
              connectionOption={connectionOption}
            />
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
          {showTestNotice && needsAuthorization && (
            <Button
              onClick={handleAuthorize}
              data-testid="authorize-integration-btn"
            >
              Authorize integration
            </Button>
          )}
          {showTestNotice && !needsAuthorization && (
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
