import { Tag, Tooltip } from "fidesui";

import type { ComplianceStatus } from "./types";

interface ComplianceBadgeProps {
  status: ComplianceStatus;
  driftCount?: number;
}

const STATUS_CONFIG: Record<
  ComplianceStatus,
  { label: (drift: number) => string; color: string; tooltip: string }
> = {
  compliant: {
    label: () => "Compliant",
    color: "success",
    tooltip: "All detected categories match defined policy",
  },
  drift: {
    label: (drift) => `Drift${drift > 0 ? ` (${drift})` : ""}`,
    color: "warning",
    tooltip:
      "Classifier detected categories outside the defined scope of this purpose",
  },
  unknown: {
    label: () => "Not scanned",
    color: "default",
    tooltip: "No detected data available yet for this purpose",
  },
};

const ComplianceBadge = ({ status, driftCount = 0 }: ComplianceBadgeProps) => {
  const config = STATUS_CONFIG[status];
  return (
    <Tooltip title={config.tooltip}>
      <Tag color={config.color}>{config.label(driftCount)}</Tag>
    </Tooltip>
  );
};

export default ComplianceBadge;
