import { AntTooltip as Tooltip, Icons } from "fidesui";

import { ConsentStatus, ConsentStatusInfo } from "~/types/api";

interface DiscoveryStatusIconProps {
  consentStatus: ConsentStatusInfo | null | undefined;
}

export const DiscoveryStatusIcon = ({
  consentStatus,
}: DiscoveryStatusIconProps) => {
  return consentStatus?.status === ConsentStatus.ALERT ? (
    <Tooltip title={consentStatus?.message}>
      <div className="mb-px" data-testid="discovery-status-icon-alert">
        {/* div wrapper helps keep tooltip accessible and icon size consistent */}
        {/* mb-px is to assist with vertical centering since the visual weight of the triangle is bottom-heavy */}
        <Icons.WarningAltFilled style={{ color: "var(--fidesui-error)" }} />
      </div>
    </Tooltip>
  ) : null;
};
