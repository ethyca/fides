import { AntTag as Tag, AntTooltip as Tooltip, Icons } from "fidesui";
import { useState } from "react";

import { ConsentStatus, StagedResourceAPIResponse } from "~/types/api";

import { ConsentBreakdownModal } from "../../ConsentBreakdownModal";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: ConsentStatus;
  stagedResource: StagedResourceAPIResponse;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  stagedResource,
}: DiscoveryStatusBadgeCellProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const handleClick = () => {
    setIsOpen(true);
  };
  const handleCancel = () => {
    setIsOpen(false);
  };
  return (
    <>
      {consentAggregated === ConsentStatus.WITHOUT_CONSENT && (
        <Tooltip title="Asset was detected before the user gave consent or without any consent. Click the info icon for more details.">
          <Tag
            color="error"
            closeIcon={<Icons.Information style={{ width: 12, height: 12 }} />}
            closeButtonLabel="View details"
            onClose={handleClick}
          >
            Without consent
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.WITH_CONSENT && (
        <Tooltip title="Asset was detected after the user gave consent">
          <Tag color="success">With consent</Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.EXEMPT && (
        <Tooltip title="Asset is valid regardless of consent">
          <Tag>Consent exempt</Tag>
        </Tooltip>
      )}
      {consentAggregated === ConsentStatus.UNKNOWN && (
        <Tooltip title="Did not find consent information for this asset. You may need to re-run the monitor.">
          <Tag>Unknown</Tag>
        </Tooltip>
      )}
      {isOpen && ( // since this component is on every row, we need to check if it's open to render it (otherwise it will render on every row)
        <ConsentBreakdownModal
          isOpen={isOpen}
          stagedResource={stagedResource}
          status={consentAggregated}
          onCancel={handleCancel}
          // onDownload={handleDownload}
        />
      )}
    </>
  );
};
