import {
  ACTION_CENTER_ROUTE,
  CONSENT_REPORTING_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";

import { ActionSeverity, ActionType, PostureBand } from "./types";

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
  PostureBand,
  { label: string; color: "success" | "info" | "caution" | "error" }
> = {
  [PostureBand.EXCELLENT]: { label: "Excellent", color: "success" },
  [PostureBand.GOOD]: { label: "Good", color: "success" },
  [PostureBand.AT_RISK]: { label: "At Risk", color: "caution" },
  [PostureBand.CRITICAL]: { label: "Critical", color: "error" },
};

export const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  [PostureBand.AT_RISK]: "warning",
  [PostureBand.CRITICAL]: "error",
};

export const URGENCY_TABS = [
  { key: "act_now", label: "Act now" },
  { key: "scheduled", label: "Scheduled" },
  { key: "when_ready", label: "When ready" },
] as const;

export type UrgencyGroup = (typeof URGENCY_TABS)[number]["key"];

export const ACTION_CTA: Record<
  ActionType,
  { label: string; route: (data: Record<string, unknown>) => string }
> = {
  [ActionType.CLASSIFICATION_REVIEW]: {
    label: "Review classifications",
    route: () => "/data-discovery/action-center",
  },
  [ActionType.DSR_ACTION]: {
    label: "View request",
    route: (d) => {
      if (d.request_id) {
        return `/privacy-requests/${d.request_id}`;
      }
      if (d.is_overdue) {
        return "/privacy-requests?is_overdue=true";
      }
      return "/privacy-requests";
    },
  },
  [ActionType.SYSTEM_REVIEW]: {
    label: "Review system",
    route: () => "/data-discovery/action-center",
  },
  [ActionType.STEWARD_ASSIGNMENT]: {
    label: "Assign steward",
    route: (d) =>
      d.system_id ? `/systems/configure/${d.system_id}` : "/systems",
  },
  [ActionType.CONSENT_ANOMALY]: {
    label: "Investigate",
    route: () => "/consent/reporting",
  },
  [ActionType.POLICY_VIOLATION]: {
    label: "Review violation",
    route: (d) =>
      d.system_id
        ? `/data-discovery/access-control?tab=log&violationId=${d.system_id}`
        : "/data-discovery/access-control",
  },
  [ActionType.PIA_UPDATE]: {
    label: "View assessment",
    route: (d) =>
      d.assessment_id
        ? `/privacy-assessments/${d.assessment_id}`
        : "/privacy-assessments",
  },
};

export const ASTRALIS_METRICS = [
  { key: "active_conversations", label: "Active" },
  { key: "awaiting_response", label: "Awaiting" },
  { key: "completed_assessments", label: "Completed" },
  { key: "risks_identified", label: "Risks" },
] as const;

export type AstralisMetricKey = (typeof ASTRALIS_METRICS)[number]["key"];

export const ASTRALIS_ACTIVE_KEY =
  "active_conversations" satisfies AstralisMetricKey;
export const ASTRALIS_AWAITING_KEY =
  "awaiting_response" satisfies AstralisMetricKey;

export function getUrgencyGroup(
  severity: ActionSeverity,
  dueDate: string | null,
): UrgencyGroup {
  if (
    severity === ActionSeverity.CRITICAL ||
    severity === ActionSeverity.HIGH
  ) {
    return "act_now";
  }
  if (dueDate) {
    return "scheduled";
  }
  return "when_ready";
}
