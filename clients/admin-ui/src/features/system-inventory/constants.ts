import { CUSTOM_TAG_COLOR } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import {
  HealthStatus,
  PillarKey,
  RiskFreshness,
  RiskSeverity,
  SystemCapability,
} from "./types";

export const HEALTH_CONFIG: Record<
  HealthStatus,
  { label: string; color: string; dotColor: string }
> = {
  [HealthStatus.HEALTHY]: {
    label: "Healthy",
    color: "success",
    dotColor: palette.FIDESUI_SUCCESS,
  },
  [HealthStatus.ISSUES]: {
    label: "Issues",
    color: "warning",
    dotColor: palette.FIDESUI_WARNING,
  },
};

export const SEVERITY_COLORS: Record<RiskSeverity, string> = {
  [RiskSeverity.CRITICAL]: palette.FIDESUI_ERROR,
  [RiskSeverity.HIGH]: palette.FIDESUI_ERROR,
  [RiskSeverity.MEDIUM]: palette.FIDESUI_WARNING,
  [RiskSeverity.LOW]: palette.FIDESUI_MINOS,
};

export const SEVERITY_LABELS: Record<RiskSeverity, string> = {
  [RiskSeverity.CRITICAL]: "Critical",
  [RiskSeverity.HIGH]: "High",
  [RiskSeverity.MEDIUM]: "Medium",
  [RiskSeverity.LOW]: "Low",
};

export const SEVERITY_WEIGHTS: Record<RiskSeverity, number> = {
  [RiskSeverity.CRITICAL]: 10,
  [RiskSeverity.HIGH]: 5,
  [RiskSeverity.MEDIUM]: 2,
  [RiskSeverity.LOW]: 1,
};

export const PILLAR_CONFIG: Record<
  PillarKey,
  { label: string; color: string; description: string }
> = {
  [PillarKey.COVERAGE]: {
    label: "Coverage",
    color: palette.FIDESUI_OLIVE,
    description:
      "How complete your inventory is: annotation, purposes, and stewards across systems.",
  },
  [PillarKey.CLASSIFICATION]: {
    label: "Classification",
    color: palette.FIDESUI_TERRACOTTA,
    description: "Share of labeled data that has been approved.",
  },
  [PillarKey.RISK]: {
    label: "Compliance",
    color: palette.FIDESUI_MINOS,
    description: "Percentage of governance checks passing across all systems.",
  },
};

export const SEVERITY_FILTER_OPTIONS = [
  {
    label: SEVERITY_LABELS[RiskSeverity.CRITICAL],
    value: RiskSeverity.CRITICAL,
  },
  { label: SEVERITY_LABELS[RiskSeverity.HIGH], value: RiskSeverity.HIGH },
  { label: SEVERITY_LABELS[RiskSeverity.MEDIUM], value: RiskSeverity.MEDIUM },
  { label: SEVERITY_LABELS[RiskSeverity.LOW], value: RiskSeverity.LOW },
];

export const FRESHNESS_FILTER_OPTIONS = [
  { label: "Detected this week", value: RiskFreshness.WEEK },
  { label: "Detected this month", value: RiskFreshness.MONTH },
  { label: "Older than a month", value: RiskFreshness.OLDER },
];

export const ROLE_COLORS: Record<string, string> = {
  producer: "default",
  consumer: "default",
};

export const SYSTEM_TYPE_OPTIONS = [
  "Data warehouse",
  "Analytics",
  "CRM",
  "Payment processor",
  "ERP",
  "Data pipeline",
  "ML training",
  "Internal service",
  "Support platform",
  "Messaging",
  "Identity provider",
  "CDP",
  "Ad platform",
  "Expense management",
  "HRIS",
  "Fraud detection",
].map((t) => ({ label: t, value: t }));

export const HEALTH_FILTER_OPTIONS = [
  { label: "Needs attention", value: HealthStatus.ISSUES },
  { label: "Healthy", value: HealthStatus.HEALTHY },
];

export const INTEGRATION_STATUS_COLORS: Record<string, string> = {
  active: "success",
  disabled: "default",
  failed: "error",
  untested: "warning",
};

export const MONITOR_STATUS_COLORS: Record<string, string> = {
  completed: "success",
  processing: "warning",
  failed: "error",
};

export const CAPABILITY_TAG_COLORS: Record<
  SystemCapability,
  `${CUSTOM_TAG_COLOR}`
> = {
  [SystemCapability.DSAR]: CUSTOM_TAG_COLOR.OLIVE,
  [SystemCapability.MONITORING]: CUSTOM_TAG_COLOR.SANDSTONE,
  [SystemCapability.CONSENT]: CUSTOM_TAG_COLOR.NECTAR,
  [SystemCapability.INTEGRATIONS]: CUSTOM_TAG_COLOR.MINOS,
  [SystemCapability.CLASSIFICATION]: CUSTOM_TAG_COLOR.TERRACOTTA,
};
