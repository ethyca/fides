import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";

import { ConsentStatus, StagedResourceAPIResponse } from "~/types/api";

import {
  DiscoveryErrorStatuses,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
} from "../../constants";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: ConsentStatus;
  stagedResource: StagedResourceAPIResponse;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  stagedResource,
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

  // Check if the asset has categories of consent
  const hasDataUses = stagedResource.data_uses
    ? stagedResource.data_uses.length > 0
    : false;

  // Determine tooltip text from the consent status
  let tagTooltip = DiscoveryStatusDescriptions[consentAggregated];

  // One exception: if the status is unknown and the asset has no categories of consent,
  // we want to nudge the user to add a category of consent instead of running the monitor
  if (consentAggregated === ConsentStatus.UNKNOWN && !hasDataUses) {
    tagTooltip =
      "Add a category of consent to this asset to find consent information.";
  }

  return (
    <Tooltip title={tagTooltip}>
      <Tag
        color={isErrorStatus ? "error" : undefined}
        data-testid={getTestId()}
      >
        {DiscoveryStatusDisplayNames[consentAggregated]}
      </Tag>
    </Tooltip>
  );
};
