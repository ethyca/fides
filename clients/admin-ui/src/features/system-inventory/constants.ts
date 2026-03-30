import { HealthStatus } from "./types";

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
  [HealthStatus.VIOLATIONS]: {
    label: "Violations",
    color: "error",
    dotColor: "#d9534f",
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
  { label: "Healthy", value: HealthStatus.HEALTHY },
  { label: "Has issues", value: HealthStatus.ISSUES },
  { label: "Has violations", value: HealthStatus.VIOLATIONS },
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
