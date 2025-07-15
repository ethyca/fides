import { AntFlex as Flex, AntTooltip as Tooltip, Text } from "fidesui";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { DiscoveryStatusIcon } from "../../DiscoveryStatusIcon";

interface DiscoveredSystemStatusCellProps {
  system: SystemStagedResourcesAggregateRecord;
}

export const DiscoveredSystemStatusCell = ({
  system,
}: DiscoveredSystemStatusCellProps) => {
  return (
    <Flex align="center">
      {!system.system_key && (
        <Tooltip title="New system">
          {/* icon has to be wrapped in a span for the tooltip to work */}
          <span>{STATUS_INDICATOR_MAP.Change}</span>
        </Tooltip>
      )}
      <Flex align="center" gap={4}>
        <Text
          fontSize="xs"
          fontWeight="semibold"
          lineHeight={4}
          overflow="hidden"
          textOverflow="ellipsis"
        >
          {system.name || "Uncategorized assets"}
        </Text>
        <DiscoveryStatusIcon consentStatus={system.consent_status} />
      </Flex>
    </Flex>
  );
};
