import { AntTag as Tag, Box, Flex, Text, Wrap } from "fidesui";

import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import { ConnectionConfigurationResponse } from "~/types/api";

const SelectableIntegrationBox = ({
  integration,
  selected = false,
  onClick,
}: {
  integration?: ConnectionConfigurationResponse;
  selected?: boolean;
  onClick?: () => void;
}) => {
  const integrationTypeInfo = getIntegrationTypeInfo(
    integration?.connection_type,
    integration?.saas_config?.type,
  );

  return (
    <Box
      borderWidth={1}
      borderColor={selected ? "black" : "gray.200"}
      backgroundColor={selected ? "gray.50" : "transparent"}
      boxShadow={selected ? "md" : "none"}
      borderRadius="lg"
      overflow="hidden"
      padding="12px"
      cursor="pointer"
      onClick={onClick}
      data-testid={`integration-info-${integration?.key}`}
    >
      <Flex>
        <ConnectionTypeLogo data={integration ?? ""} boxSize="40px" />
        <Flex
          direction="column"
          flexGrow={1}
          marginLeft="12px"
          marginRight="60px"
        >
          <Text color="gray.700" fontWeight="semibold" fontSize="sm">
            {integration?.name || "(No name)"}
          </Text>
          <Text color="gray.600" fontSize="xs" mt={1}>
            {integrationTypeInfo.category}
          </Text>
        </Flex>
      </Flex>
      <Wrap marginTop="12px" spacing={1}>
        {integrationTypeInfo.tags.slice(0, 3).map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
        {integrationTypeInfo.tags.length > 3 && (
          <Tag color="corinth">+{integrationTypeInfo.tags.length - 3}</Tag>
        )}
      </Wrap>
    </Box>
  );
};

export default SelectableIntegrationBox;
