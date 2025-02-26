import { h } from "preact";

import { GpcStatus } from "../lib/consent-types";
import { useI18n } from "../lib/i18n/i18n-context";

export const GpcBadge = ({ status }: { status: GpcStatus }) => {
  const { i18n } = useI18n();
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
