import {
  ACTION_CENTER_ROUTE,
  CONSENT_REPORTING_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";

import type { ActivityFeedItem } from "./types";
import { ActionSeverity, ActionType, PostureBand } from "./types";

export const DIMENSION_DESCRIPTIONS: Record<string, string> = {
  coverage: "Percentage of data systems that are mapped and documented",
  classification_health:
    "Accuracy and completeness of data classification labels across classified fields",
  dsr_compliance:
    "Timeliness and completeness of data subject request processing",
  consent_alignment:
    "Alignment between collected consent records and actual data processing activities",
};

export const DIMENSION_LABELS: Record<string, string> = {
  coverage: "Data Coverage",
  classification_health: "Classification Health",
  dsr_compliance: "DSR Health",
  consent_alignment: "Consent Health",
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
  { key: "overdue", label: "Overdue" },
  { key: "urgent", label: "Requires Attention" },
  { key: "pending", label: "Pending" },
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

export const ACTIVITY_FILTER_OPTIONS = [
  { label: "All", value: "all" },
  { label: "Human", value: "user" },
  { label: "System", value: "system" },
] as const;

export const EVENT_SOURCE_LABELS: Record<
  NonNullable<ActivityFeedItem["event_source"]>,
  string
> = {
  helios: "Helios",
  janus: "Janus",
  lethe: "Lethe",
  astralis: "Astralis",
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
export const ASTRALIS_RISKS_KEY =
  "risks_identified" satisfies AstralisMetricKey;

export function getUrgencyGroup(
  severity: ActionSeverity,
  dueDate: string | null,
): UrgencyGroup {
  // Past due date → Overdue, regardless of severity
  // Normalize to end-of-day to avoid timezone boundary issues with date-only strings
  if (dueDate) {
    const due = new Date(dueDate);
    due.setHours(23, 59, 59, 999);
    if (due < new Date()) {
      return "overdue";
    }
  }
  // High severity but not overdue → Requires Attention
  if (
    severity === ActionSeverity.CRITICAL ||
    severity === ActionSeverity.HIGH
  ) {
    return "urgent";
  }
  // Everything else
  return "pending";
}
