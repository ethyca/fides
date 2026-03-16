import {
  ACTION_CENTER_ROUTE,
  CONSENT_REPORTING_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";

export const DIMENSION_DESCRIPTIONS: Record<string, string> = {
  coverage: "How well your data systems are mapped and documented",
  classification_health:
    "Accuracy and completeness of data classification labels",
  dsr_compliance: "Timeliness and completeness of data subject requests",
  consent_alignment: "Alignment between collected consent and data processing",
};

export const DIMENSION_LABELS: Record<string, string> = {
  coverage: "Coverage",
  classification_health: "Classification Health",
  dsr_compliance: "DSR Compliance",
  consent_alignment: "Consent Alignment",
};

export const DIMENSION_ROUTES: Record<
  string,
  { label: string; route: string }
> = {
  coverage: { label: "View systems", route: SYSTEM_ROUTE },
  classification_health: {
    label: "Review classifications",
    route: ACTION_CENTER_ROUTE,
  },
  dsr_compliance: {
    label: "View privacy requests",
    route: PRIVACY_REQUESTS_ROUTE,
  },
  consent_alignment: {
    label: "View consent",
    route: CONSENT_REPORTING_ROUTE,
  },
};

export const BAND_CONFIG: Record<
  string,
  { label: string; color: "success" | "info" | "caution" | "error" }
> = {
  excellent: { label: "Excellent", color: "success" },
  good: { label: "Good", color: "success" },
  at_risk: { label: "At Risk", color: "caution" },
  critical: { label: "Critical", color: "error" },
};

export const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  at_risk: "warning",
  critical: "error",
};
