import type { ConsumerType } from "./types";

// --- Legacy constants (used by DataConsumerForm.tsx, DataConsumerActionsCell.tsx) ---

export enum DataConsumerType {
  SERVICE = "service",
  APPLICATION = "application",
  GROUP = "group",
  USER = "user",
}

export const CONSUMER_TYPE_LABELS: Record<DataConsumerType, string> = {
  [DataConsumerType.SERVICE]: "Service",
  [DataConsumerType.APPLICATION]: "Application",
  [DataConsumerType.GROUP]: "Group",
  [DataConsumerType.USER]: "User",
};

export const CONSUMER_TYPE_OPTIONS = Object.entries(CONSUMER_TYPE_LABELS).map(
  ([value, label]) => ({ value, label }),
);

export const DATA_CONSUMER_FORM_ID = "data-consumer-form";

// --- New UI constants for the redesigned list view ---

export const CONSUMER_TYPE_UI_LABELS: Record<ConsumerType, string> = {
  team: "Team",
  ai_agent: "AI agent",
  project: "Project",
  system: "System",
  service_account: "Service account",
};

export const CONSUMER_TYPE_UI_OPTIONS = Object.entries(
  CONSUMER_TYPE_UI_LABELS,
).map(([value, label]) => ({ value, label }));

export const PLATFORM_LABELS: Record<string, string> = {
  google_groups: "Google Groups",
  service_account: "Service account",
  okta: "Okta",
  active_directory: "Active Directory",
};

export const PLATFORM_OPTIONS = Object.entries(PLATFORM_LABELS).map(
  ([value, label]) => ({ value, label }),
);

export type StatusFilterValue = "has_findings" | "no_purposes" | "healthy";

export const STATUS_FILTER_OPTIONS: { value: StatusFilterValue; label: string }[] = [
  { value: "has_findings", label: "Has findings" },
  { value: "no_purposes", label: "No purposes" },
  { value: "healthy", label: "Healthy" },
];
