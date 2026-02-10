import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraText as Text,
  ChakraWrap as Wrap,
  Icons,
  Tag,
  Tooltip,
} from "fidesui";
import { ReactNode } from "react";

import { useConnectionLogo } from "~/features/common/hooks";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import DeleteConnectionModal from "~/features/datastore-connections/DeleteConnectionModal";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import { useIntegrationAuthorization } from "~/features/integrations/hooks/useIntegrationAuthorization";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionConfigurationResponse } from "~/types/api";

const IntegrationBox = ({
  integration,
  integrationTypeInfo,
  showTestNotice,
  otherButtons,
  showDeleteButton,
  configureButtonLabel = "Configure",
  onConfigureClick,
}: {
  integration?: ConnectionConfigurationResponse;
  integrationTypeInfo?: IntegrationTypeInfo;
  showTestNotice?: boolean;
  otherButtons?: ReactNode;
  showDeleteButton?: boolean;
  configureButtonLabel?: string;
  onConfigureClick?: () => void;
}) => {
  const { testConnection, isLoading, testData } =
    useTestConnection(integration);

  // Get logo data using the custom hook
  const logoData = useConnectionLogo(integration);

  // Fetch connection types for SAAS integration generation
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = connectionTypesData?.items || [];

  // Use provided integrationTypeInfo or fallback to generating it
  const typeInfo =
    integrationTypeInfo ||
    getIntegrationTypeInfo(
      integration?.connection_type,
      integration?.saas_config?.type,
      connectionTypes,
    );

  const connectionOption = useIntegrationOption(
    integration?.connection_type,
    integration?.saas_config?.type as SaasConnectionTypes,
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
        <ConnectionTypeLogo data={logoData} size={50} />
        <Flex direction="column" flexGrow={1} marginLeft="16px">
          <Flex alignItems="center" gap={2}>
            <Text color="gray.700" fontWeight="semibold">
              {integration?.name || "(No name)"}
            </Text>
            {connectionOption?.custom && (
              <Tooltip title="Custom integration" placement="top">
                <Box as="span" display="inline-flex">
                  <Icons.SettingsCheck size={16} />
                </Box>
              </Tooltip>
            )}
            {otherButtons}
          </Flex>
          {showTestNotice ? (
            <ConnectionStatusNotice
              testData={testData}
              connectionOption={connectionOption}
            />
          ) : (
            <Text color="gray.700" fontSize="sm" fontWeight="semibold" mt={1}>
              {getCategoryLabel(typeInfo.category)}
            </Text>
          )}
        </Flex>
        <div className="ml-auto flex shrink-0 gap-4">
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
          {onConfigureClick && (
            <Button onClick={onConfigureClick} data-testid="configure-btn">
              {configureButtonLabel}
            </Button>
          )}
        </div>
      </Flex>
      <Wrap marginTop="16px">
        {typeInfo.tags.map((item: string) => (
          <Tag key={item}>{item}</Tag>
        ))}
      </Wrap>
    </Box>
  );
};

export default IntegrationBox;
