import { AntTooltip as Tooltip, Icons } from "fidesui";

import { MonitorConsentStatus } from "../types";

export const DiscoveryStatusIcon = ({
  consentStatus,
}: {
  consentStatus: MonitorConsentStatus | undefined;
}) => {
  return !consentStatus?.status ? (
    <Tooltip title="{consentStatus?.message}">
      <div>
        {/* div wrapper helps keep tooltip accessible and icon size consistent */}
        <Icons.WarningAltFilled
          className="ml-1 inline-block align-middle"
          style={{ color: "var(--fidesui-error)" }}
        />
      </div>
    </Tooltip>
  ) : null;
};
