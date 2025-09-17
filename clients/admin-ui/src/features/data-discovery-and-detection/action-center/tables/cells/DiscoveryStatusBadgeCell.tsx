import { AntTag as Tag, AntTooltip as Tooltip, Icons } from "fidesui";

import { ConsentStatus, StagedResourceAPIResponse } from "~/types/api";

import {
  ConsentStatusType,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
  DiscoveryStatusTypeMapping,
} from "../../constants";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: ConsentStatus;
  stagedResource: StagedResourceAPIResponse;
  onShowBreakdown?: (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => void;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  stagedResource,
  onShowBreakdown,
}: DiscoveryStatusBadgeCellProps) => {
  const handleClick = () => {
    onShowBreakdown?.(stagedResource, consentAggregated);
  };

  const statusType = DiscoveryStatusTypeMapping[consentAggregated];
  const isErrorStatus = statusType === ConsentStatusType.ERROR;

  const getTagColor = (): "success" | "error" | undefined => {
    switch (statusType) {
      case ConsentStatusType.SUCCESS:
        return "success";
      case ConsentStatusType.ERROR:
        return "error";
      default:
        return undefined;
    }
  };

  const getTestId = (): string => {
    return `status-badge_${consentAggregated.replace(/_/g, "-")}`;
  };

  return (
    <Tooltip title={DiscoveryStatusDescriptions[consentAggregated]}>
      <Tag
        color={getTagColor()}
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
