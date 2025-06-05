import { AntTooltip as Tooltip, Flex, Text } from "fidesui";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

interface DiscoveredSystemStatusCellProps {
  system: SystemStagedResourcesAggregateRecord;
}

export const DiscoveredSystemStatusCell = ({
  system,
}: DiscoveredSystemStatusCellProps) => {
  return (
    <Flex alignItems="center" height="100%">
      {!system?.system_key && (
        <Tooltip title="New system">
          {/* icon has to be wrapped in a span for the tooltip to work */}
          <span>{STATUS_INDICATOR_MAP.Change}</span>
        </Tooltip>
      )}
      <Text
        fontSize="xs"
        fontWeight="semibold"
        lineHeight={4}
        overflow="hidden"
        textOverflow="ellipsis"
      >
        {system?.name || "Uncategorized assets"}
      </Text>
    </Flex>
  );
};
