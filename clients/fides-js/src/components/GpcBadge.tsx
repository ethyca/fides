import { h } from "preact";

import { GpcStatus } from "../lib/consent-types";
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
