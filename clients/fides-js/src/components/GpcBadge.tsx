import { h } from "preact";
import { GpcStatus, PrivacyNotice } from "../lib/consent-types";
import { getConsentContext } from "../lib/consent-context";
import { getGpcStatusFromNotice } from "../lib/consent-utils";

export const GpcBadge = ({ status }: { status: GpcStatus }) => {
  if (status === GpcStatus.NONE) {
    return null;
  }
  return (
    <span className="fides-gpc-label">
      Global Privacy Control{" "}
      <span className={`fides-gpc-badge fides-gpc-badge-${status.valueOf()}`}>
        {status.valueOf()}
      </span>
    </span>
  );
};

export const GpcBadgeForNotice = ({
  value,
  notice,
}: {
  value: boolean;
  notice: PrivacyNotice;
}) => {
  const consentContext = getConsentContext();
  const status = getGpcStatusFromNotice({ value, notice, consentContext });

  return <GpcBadge status={status} />;
};
