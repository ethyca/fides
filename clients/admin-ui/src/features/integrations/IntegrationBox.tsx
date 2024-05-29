import { Box, Flex, Text } from "fidesui";
import { ReactNode } from "react";

import Tag from "~/features/common/Tag";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const BIGQUERY_TAGS = ["Data Warehouse", "BigQuery", "Discovery", "Inventory"];

const IntegrationBox = ({
  integration,
  renderTestNotice,
  button,
}: {
  integration?: ConnectionConfigurationResponse;
  renderTestNotice?: boolean;
  button?: ReactNode;
}) => {
  const renderLogo = () => (
    <ConnectionTypeLogo data={integration ?? ""} boxSize="50px" />
  );

  const renderIntegrationNameContainer = () => (
    <Flex direction="column" flexGrow={1} marginLeft="16px">
      <Text color="gray.700" fontWeight="semibold">
        {integration?.name || "(No name)"}
      </Text>
      {renderTestNotice ? (
        <ConnectionStatusNotice
          timestamp={integration?.last_test_timestamp}
          succeeded={integration?.last_test_succeeded}
        />
      ) : (
        <Text color="gray.700" fontSize="sm" fontWeight="semibold" mt={1}>
          Data Warehouse
        </Text>
      )}
    </Flex>
  );

  const renderTags = () => (
    <>
      {BIGQUERY_TAGS.map((item) => (
        <Tag key={item}>{item}</Tag>
      ))}
    </>
  );

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
        {renderLogo()}
        {renderIntegrationNameContainer()}
        {button}
      </Flex>
      <Flex marginTop="16px">{renderTags()}</Flex>
    </Box>
  );
};

export default IntegrationBox;
