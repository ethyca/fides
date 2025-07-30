import {
  AntButton as Button,
  AntTag as Tag,
  Box,
  Flex,
  Text,
  Wrap,
} from "fidesui";

import { useConnectionLogo } from "~/features/common/hooks";
import useClickOutside from "~/features/common/hooks/useClickOutside";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import { ConnectionConfigurationResponse } from "~/types/api";

const SelectableIntegrationBox = ({
  integration,
  selected = false,
  onClick,
  onDetailsClick,
  onUnfocus,
}: {
  integration?: ConnectionConfigurationResponse;
  selected?: boolean;
  onClick?: () => void;
  onDetailsClick?: () => void;
  onUnfocus?: () => void;
}) => {
  // Get logo data using the custom hook
  const logoData = useConnectionLogo(integration);

  const integrationTypeInfo = getIntegrationTypeInfo(
    integration?.connection_type,
    integration?.saas_config?.type,
  );

  // Handle click outside to unfocus when selected
  const boxRef = useClickOutside<HTMLDivElement>(() => {
    if (selected && onUnfocus) {
      onUnfocus();
    }
  });

  return (
    <Box
      ref={boxRef}
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
      <Flex justifyContent="space-between" alignItems="flex-start">
        <Flex flexGrow={1}>
          <ConnectionTypeLogo data={logoData ?? ""} boxSize="40px" />
          <Flex
            direction="column"
            flexGrow={1}
            marginLeft="12px"
            marginRight="12px"
          >
            <Text color="gray.700" fontWeight="semibold" fontSize="sm">
              {integration?.name || "(No name)"}
            </Text>
            <Text color="gray.600" fontSize="xs" mt={1}>
              {integrationTypeInfo.category}
            </Text>
          </Flex>
        </Flex>
        {onDetailsClick && (
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDetailsClick();
            }}
            type="default"
            className="px-2 py-1 text-xs"
            data-testid={`details-btn-${integration?.key}`}
          >
            Details
          </Button>
        )}
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
