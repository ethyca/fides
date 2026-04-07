import { CUSTOM_TAG_COLOR } from "fidesui";

import { HealthStatus, SystemCapability } from "./types";

export const HEALTH_CONFIG: Record<
  HealthStatus,
  { label: string; color: string; dotColor: string }
> = {
  [HealthStatus.HEALTHY]: {
    label: "Healthy",
    color: "success",
    dotColor: "#5a9a68",
  },
  [HealthStatus.ISSUES]: {
    label: "Issues",
    color: "warning",
    dotColor: "#e59d47",
  },
};

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

export const CAPABILITY_TAG_COLORS: Record<SystemCapability, `${CUSTOM_TAG_COLOR}`> = {
  [SystemCapability.DSAR]: CUSTOM_TAG_COLOR.OLIVE,
  [SystemCapability.MONITORING]: CUSTOM_TAG_COLOR.SANDSTONE,
  [SystemCapability.CONSENT]: CUSTOM_TAG_COLOR.NECTAR,
  [SystemCapability.INTEGRATIONS]: CUSTOM_TAG_COLOR.MINOS,
  [SystemCapability.CLASSIFICATION]: CUSTOM_TAG_COLOR.TERRACOTTA,
};
