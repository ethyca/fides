import { Box, Button, ButtonGroup, Flex, Text } from "fidesui";

import Tag from "~/features/common/Tag";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const BIGQUERY_TAGS = ["Data Warehouse", "BigQuery", "Discovery", "Inventory"];

const IntegrationBox = ({
  integration,
  showTestNotice,
  buttonLabel = "Configure",
  onConfigureClick,
}: {
  integration?: ConnectionConfigurationResponse;
  showTestNotice?: boolean;
  buttonLabel?: string;
  onConfigureClick?: () => void;
}) => {
  const { testConnection, isLoading, testData } =
    useTestConnection(integration);

  return (
    <Box
      maxW="760px"
      borderWidth={1}
      borderRadius="lg"
      overflow="hidden"
      height="114px"
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
              Data Warehouse
            </Text>
          )}
        </Flex>
        <ButtonGroup size="sm" variant="outline">
          {showTestNotice && (
            <Button onClick={testConnection} isLoading={isLoading}>
              Test connection
            </Button>
          )}
          {onConfigureClick && (
            <Button onClick={onConfigureClick} data-testid="configure-btn">
              {buttonLabel}
            </Button>
          )}
        </ButtonGroup>
      </Flex>
      <Flex marginTop="16px">
        {BIGQUERY_TAGS.map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
      </Flex>
    </Box>
  );
};

export default IntegrationBox;
