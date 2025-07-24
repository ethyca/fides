import { AntSpace as Space, AntTooltip as Tooltip } from "fidesui";

import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { DiscoveryStatusIcon } from "../../DiscoveryStatusIcon";

interface DiscoveredSystemStatusCellProps {
  system: SystemStagedResourcesAggregateRecord;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const DiscoveredSystemStatusCell = ({
  system,
  rowClickUrl,
}: DiscoveredSystemStatusCellProps) => {
  const url = rowClickUrl?.(system);
  return (
    <Space className="max-w-[250px] flex-nowrap">
      {!system.system_key && (
        <Tooltip title="New system">
          {/* icon has to be wrapped in a span for the tooltip to work */}
          <span>{STATUS_INDICATOR_MAP.Change}</span>
        </Tooltip>
      )}
      <LinkCell
        href={url}
        data-testid={url ? "system-name-link" : "system-name-text"}
      >
        {system.name || "Uncategorized assets"}
      </LinkCell>
      <DiscoveryStatusIcon consentStatus={system.consent_status} />
    </Space>
  );
};
