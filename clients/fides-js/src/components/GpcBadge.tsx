import { GpcStatus } from "../lib/consent-types";
import { useI18n } from "../lib/i18n/i18n-context";

export const GpcBadge = ({
  status,
  ...props
}: {
  status: GpcStatus;
} & React.HTMLAttributes<HTMLSpanElement>) => {
  const { i18n } = useI18n();
  const gpcLabel = i18n.t("exp.gpc_label");
  const statusValue = status.valueOf();
  let statusLabel = "";
  if (status === GpcStatus.APPLIED) {
    statusLabel = i18n.t("exp.gpc_status_applied_label");
  } else if (status === GpcStatus.OVERRIDDEN) {
    statusLabel = i18n.t("exp.gpc_status_overridden_label");
  } else if (status === GpcStatus.NONE) {
    return null;
  }

  return (
    <span className="fides-gpc-label" {...props}>
      {gpcLabel}{" "}
      <span className={`fides-gpc-badge fides-gpc-badge-${statusValue}`}>
        {statusLabel}
      </span>
    </span>
  );
};
