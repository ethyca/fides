import { AntTooltip as Tooltip, Icons } from "fidesui";

import { AlertLevel, ConsentAlertInfo } from "~/types/api";

interface DiscoveryStatusIconProps {
  consentStatus: ConsentAlertInfo | null | undefined;
}

export const DiscoveryStatusIcon = ({
  consentStatus,
}: DiscoveryStatusIconProps) => {
  return consentStatus?.status === AlertLevel.ALERT ? (
    <Tooltip title={consentStatus?.message}>
      <div className="mb-px" data-testid="discovery-status-icon-alert">
        {/* div wrapper helps keep tooltip accessible and icon size consistent */}
        {/* mb-px is to assist with vertical centering since the visual weight of the triangle is bottom-heavy */}
        <Icons.WarningAltFilled style={{ color: "var(--fidesui-error)" }} />
      </div>
    </Tooltip>
  ) : null;
};
