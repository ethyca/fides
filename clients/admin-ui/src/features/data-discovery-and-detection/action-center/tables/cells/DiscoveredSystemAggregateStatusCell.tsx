import {
  AntFlex as Flex,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { DiscoveryStatusIcon } from "../../DiscoveryStatusIcon";

const { Link } = Typography;

interface DiscoveredSystemStatusCellProps {
  system: SystemStagedResourcesAggregateRecord;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const DiscoveredSystemStatusCell = ({
  system,
  rowClickUrl,
}: DiscoveredSystemStatusCellProps) => {
  return (
    <Flex align="center">
      {!system.system_key && (
        <Tooltip title="New system">
          {/* icon has to be wrapped in a span for the tooltip to work */}
          <span>{STATUS_INDICATOR_MAP.Change}</span>
        </Tooltip>
      )}
      <Flex align="center" gap={4} className="max-w-[250px] flex-nowrap">
        <Link
          size="sm"
          strong
          ellipsis
          href={rowClickUrl?.(system)}
          onClick={(e) => e.stopPropagation()}
          data-testid="system-name-link"
        >
          {system.name || "Uncategorized assets"}
        </Link>
        <DiscoveryStatusIcon consentStatus={system.consent_status} />
      </Flex>
    </Flex>
  );
};
