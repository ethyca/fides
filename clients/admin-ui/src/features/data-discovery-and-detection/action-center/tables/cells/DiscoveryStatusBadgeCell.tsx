import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";

import { ConsentStatus } from "~/types/api";

import {
  DiscoveryErrorStatuses,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
} from "../../constants";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: ConsentStatus;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
}: DiscoveryStatusBadgeCellProps) => {
  const isErrorStatus = DiscoveryErrorStatuses.includes(consentAggregated);

  // We only want to show compliance issues or unknown statuses
  // as the other statuses are not actionable
  const showTag = isErrorStatus || consentAggregated === ConsentStatus.UNKNOWN;
  if (!showTag) {
    return null;
  }

  const getTestId = (): string => {
    return `status-badge_${consentAggregated.replace(/_/g, "-")}`;
  };

  return (
    <Tooltip title={DiscoveryStatusDescriptions[consentAggregated]}>
      <Tag
        color={isErrorStatus ? "error" : undefined}
        data-testid={getTestId()}
      >
        {DiscoveryStatusDisplayNames[consentAggregated]}
      </Tag>
    </Tooltip>
  );
};
