import { AntTooltip as Tooltip, Icons } from "fidesui";

import { useFeatures } from "~/features/common/features/features.slice";
import { AlertLevel, ConsentAlertInfo } from "~/types/api";

interface DiscoveryStatusIconProps {
  consentStatus: ConsentAlertInfo | null | undefined;
}

export const DiscoveryStatusIcon = ({
  consentStatus,
}: DiscoveryStatusIconProps) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;

  return assetConsentStatusLabels &&
    consentStatus?.status === AlertLevel.ALERT ? (
    <Tooltip
      title={consentStatus?.message}
      data-testid="discovery-status-icon-alert-tooltip"
    >
      <div className="mb-px" data-testid="discovery-status-icon-alert">
        {/* div wrapper helps keep tooltip accessible and icon size consistent */}
        {/* mb-px is to assist with vertical centering since the visual weight of the triangle is bottom-heavy */}
        <Icons.WarningAltFilled style={{ color: "var(--fidesui-error)" }} />
      </div>
    </Tooltip>
  ) : null;
};
