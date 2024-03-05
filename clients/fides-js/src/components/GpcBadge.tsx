import { h } from "preact";
import { GpcStatus, PrivacyNotice } from "../lib/consent-types";
import { getConsentContext } from "../lib/consent-context";
import { getGpcStatusFromNotice } from "../lib/consent-utils";
import type { I18n } from "../lib/i18n";

export const GpcBadge = ({
  i18n,
  status,
}: {
  i18n: I18n;
  status: GpcStatus;
}) => {
  const gpcLabel = i18n.t("static.gpc");
  const statusValue = status.valueOf();
  let statusLabel = "";
  if (status === GpcStatus.APPLIED) {
    statusLabel = i18n.t("static.gpc.status.applied");
  } else if (status === GpcStatus.OVERRIDDEN) {
    statusLabel = i18n.t("static.gpc.status.overridden");
  } else if (status === GpcStatus.NONE) {
    // TODO (PROD-1597): check to see if this is safe to add; previously we'd render the label but no status badge
    return null;
  }

  return (
    <span className="fides-gpc-label">
      {gpcLabel}{" "}
      <span className={`fides-gpc-badge fides-gpc-badge-${statusValue}`}>
        {statusLabel}
      </span>
    </span>
  );
};

// TODO (PROD-1597): delete
export const GpcBadgeForNotice = ({
  i18n,
  value,
  notice,
}: {
  i18n: I18n;
  value: boolean;
  notice: PrivacyNotice;
}) => {
  const consentContext = getConsentContext();
  const status = getGpcStatusFromNotice({ value, notice, consentContext });

  if (status === GpcStatus.NONE) {
    return null;
  }

  return <GpcBadge i18n={i18n} status={status} />;
};
