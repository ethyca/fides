import { h } from "preact";
import { GpcStatus, PrivacyNotice } from "../lib/consent-types";
import { getConsentContext } from "../lib/consent-context";
import { getGpcStatusFromNotice } from "../lib/consent-utils";

export const GpcBadge = ({
  label,
  status,
}: {
  label: string;
  status: string;
}) => (
  <span className="fides-gpc-label">
    {label}{" "}
    <span className={`fides-gpc-badge fides-gpc-badge-${status}`}>
      {status}
    </span>
  </span>
);

export const GpcBadgeForNotice = ({
  value,
  notice,
}: {
  value: boolean;
  notice: PrivacyNotice;
}) => {
  const consentContext = getConsentContext();
  const status = getGpcStatusFromNotice({ value, notice, consentContext });

  if (status === GpcStatus.NONE) {
    return null;
  }

  return <GpcBadge label="Global Privacy Control" status={status.valueOf()} />;
};
