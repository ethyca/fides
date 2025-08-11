import {
  AntButton as Button,
  AntTag as Tag,
  AntTypography as Typography,
  Box,
  Flex,
  Text,
  Wrap,
} from "fidesui";

import { useConnectionLogo } from "~/features/common/hooks";
import useClickOutside from "~/features/common/hooks/useClickOutside";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionConfigurationResponse } from "~/types/api";

const SelectableIntegrationBox = ({
  integration,
  integrationTypeInfo,
  selected = false,
  onClick,
  onDetailsClick,
  onUnfocus,
}: {
  integration?: ConnectionConfigurationResponse;
  integrationTypeInfo?: IntegrationTypeInfo;
  selected?: boolean;
  onClick?: () => void;
  onDetailsClick?: () => void;
  onUnfocus?: () => void;
}) => {
  // Get logo data using the custom hook
  const logoData = useConnectionLogo(integration);

  // Use provided integrationTypeInfo or fallback to generating it
  const typeInfo =
    integrationTypeInfo ||
    getIntegrationTypeInfo(
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
      <Flex justifyContent="space-between" alignItems="flex-start" width="100%">
        <Flex flexGrow={1} width="100%">
          <ConnectionTypeLogo
            data={logoData ?? ""}
            boxSize="40px"
            className="shrink-0"
          />
          <Flex
            direction="column"
            flexGrow={1}
            flexShrink={1}
            marginLeft="12px"
            marginRight="12px"
            width={0}
          >
            <Typography.Text
              strong
              style={{
                color: "var(--chakra-colors-gray-700)",
                fontSize: "14px",
              }}
              ellipsis={{
                tooltip: integration?.name || "(No name)",
              }}
            >
              {integration?.name || "(No name)"}
            </Typography.Text>
            <Text color="gray.600" fontSize="xs" mt={1}>
              {getCategoryLabel(typeInfo.category)}
            </Text>
          </Flex>
          {onDetailsClick && (
            <Button
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onDetailsClick();
              }}
              type="default"
              className="shrink-0 px-2 py-1 text-xs"
              data-testid={`details-btn-${integration?.key}`}
            >
              Details
            </Button>
          )}
        </Flex>
      </Flex>
      <Wrap marginTop="12px" spacing={1}>
        {typeInfo.tags.slice(0, 3).map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
        {typeInfo.tags.length > 3 && (
          <Tag color="corinth">+{typeInfo.tags.length - 3}</Tag>
        )}
      </Wrap>
    </Box>
  );
};

export default SelectableIntegrationBox;
