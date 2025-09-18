import { AntTag as Tag, AntTooltip as Tooltip, Icons } from "fidesui";

import { ConsentStatus, StagedResourceAPIResponse } from "~/types/api";

import {
  DiscoveryErrorStatuses,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
} from "../../constants";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: ConsentStatus;
  stagedResource: StagedResourceAPIResponse;
  showComplianceIssueDetails?: (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => void;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  stagedResource,
  showComplianceIssueDetails,
}: DiscoveryStatusBadgeCellProps) => {
  const handleClick = () => {
    showComplianceIssueDetails?.(stagedResource, consentAggregated);
  };

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
        closeIcon={
          isErrorStatus ? (
            <Icons.Information style={{ width: 12, height: 12 }} />
          ) : undefined
        }
        closeButtonLabel={isErrorStatus ? "View details" : undefined}
        onClose={isErrorStatus ? handleClick : undefined}
        data-testid={getTestId()}
      >
        {DiscoveryStatusDisplayNames[consentAggregated]}
      </Tag>
    </Tooltip>
  );
};
