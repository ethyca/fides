import { GpcStatus } from "../lib/consent-types";
import { messageExists } from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";

export const GpcBadge = ({
  status,
  ...props
}: {
  status: GpcStatus;
} & React.HTMLAttributes<HTMLSpanElement>) => {
  const { i18n } = useI18n();
  // Use dynamic translation if available, otherwise fallback to static
  const gpcLabel = messageExists(i18n, "exp.gpc_label")
    ? i18n.t("exp.gpc_label")
    : i18n.t("static.gpc");
  const statusValue = status.valueOf();
  let statusLabel = "";
  if (status === GpcStatus.APPLIED) {
    statusLabel = messageExists(i18n, "exp.gpc_status_applied_label")
      ? i18n.t("exp.gpc_status_applied_label")
      : i18n.t("static.gpc.status.applied");
  } else if (status === GpcStatus.OVERRIDDEN) {
    statusLabel = messageExists(i18n, "exp.gpc_status_overridden_label")
      ? i18n.t("exp.gpc_status_overridden_label")
      : i18n.t("static.gpc.status.overridden");
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
