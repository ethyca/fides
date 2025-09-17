import { AntTag as Tag, AntTooltip as Tooltip, Icons } from "fidesui";

import { ConsentStatus, StagedResourceAPIResponse } from "~/types/api";

import { DiscoveryStatusDisplayNames } from "../../constants";

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

  return (
    <>
      {consentAggregated === ConsentStatus.WITHOUT_CONSENT && (
        <Tooltip title="Asset was detected without any consent. Click the info icon for more details.">
          <Tag
            color="error"
            closeIcon={<Icons.Information style={{ width: 12, height: 12 }} />}
            closeButtonLabel="View details"
            onClose={handleClick}
            data-testid="status-badge_without-consent"
          >
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.PRE_CONSENT && (
        <Tooltip title="Assets loaded before the user had a chance to give consent. This violates opt-in compliance requirements if your CMP is configured for explicit consent.">
          <Tag
            color="error"
            closeIcon={<Icons.Information style={{ width: 12, height: 12 }} />}
            closeButtonLabel="View details"
            onClose={handleClick}
            data-testid="status-badge_pre-consent"
          >
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.WITH_CONSENT && (
        <Tooltip title="Asset was detected after the user gave consent">
          <Tag color="success" data-testid="status-badge_with-consent">
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.EXEMPT && (
        <Tooltip title="Asset is valid regardless of consent">
          <Tag data-testid="status-badge_consent-exempt">
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.UNKNOWN && (
        <Tooltip title="Did not find consent information for this asset. You may need to re-run the monitor.">
          <Tag data-testid="status-badge_unknown">
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.NOT_APPLICABLE && (
        <Tooltip title="No privacy notices apply to this asset">
          <Tag data-testid="status-badge_not-applicable">
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.CMP_ERROR && (
        <Tooltip title="The Consent Management Platform (CMP) was not detected when the service ran. It likely failed to load or wasn't available.">
          <Tag data-testid="status-badge_cmp-error">
            {DiscoveryStatusDisplayNames[consentAggregated]}
          </Tag>
        </Tooltip>
      )}
    </>
  );
};
