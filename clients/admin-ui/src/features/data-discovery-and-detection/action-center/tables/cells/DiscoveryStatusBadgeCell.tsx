import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { AggregatedConsent } from "~/types/api";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: AggregatedConsent;
  dateDiscovered: string | null | undefined;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  dateDiscovered,
}: DiscoveryStatusBadgeCellProps) => {
  return (
    <Tooltip title={dateDiscovered ? formatDate(dateDiscovered) : undefined}>
      {/* tooltip throws errors if immediate child is not available or changes after render so this div wrapper helps keep it stable */}
      {consentAggregated === AggregatedConsent.WITH_CONSENT && (
        <Tag color="success">With consent</Tag>
      )}
      {consentAggregated === AggregatedConsent.WITHOUT_CONSENT && (
        <Tag color="error">Without consent</Tag>
      )}
      {consentAggregated === AggregatedConsent.EXEMPT && (
        <Tag>Consent exempt</Tag>
      )}
      {consentAggregated === AggregatedConsent.UNKNOWN && <Tag>Unknown</Tag>}
    </Tooltip>
  );
};
