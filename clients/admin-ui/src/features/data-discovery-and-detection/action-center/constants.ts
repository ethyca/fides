import { CUSTOM_TAG_COLOR } from "fidesui";

import {
  ConsentStatus,
  DatastoreMonitorUpdates,
  DiffStatus,
  WebMonitorUpdates,
} from "~/types/api";

import { ActionCenterTabHash } from "./hooks/useActionCenterTabs";

export const DiscoveryStatusDisplayNames: Record<ConsentStatus, string> = {
  [ConsentStatus.WITH_CONSENT]: "Consent respected",
  [ConsentStatus.WITHOUT_CONSENT]: "Consent ignored",
  [ConsentStatus.EXEMPT]: "Exempt",
  [ConsentStatus.UNKNOWN]: "Unknown",
  [ConsentStatus.PRE_CONSENT]: "Pre-Consent",
  [ConsentStatus.CMP_ERROR]: "CMP failure",
  [ConsentStatus.NOT_APPLICABLE]: "Not applicable",
};

export const DiscoveryStatusDescriptions: Record<ConsentStatus, string> = {
  [ConsentStatus.WITH_CONSENT]:
    "Asset was detected after the user gave consent",
  [ConsentStatus.WITHOUT_CONSENT]:
    "The user explicitly opted out, but this asset still loaded. This is a serious compliance issue and may indicate that consent settings are not being enforced.",
  [ConsentStatus.EXEMPT]: "Asset is valid regardless of consent",
  [ConsentStatus.UNKNOWN]:
    "Did not find consent information for this asset. You may need to re-run the monitor.",
  [ConsentStatus.PRE_CONSENT]:
    "Assets loaded before the user had a chance to give consent. This violates opt-in compliance requirements if your CMP is configured for explicit consent.",
  [ConsentStatus.CMP_ERROR]:
    "The Consent Management Platform (CMP) was not detected when the service ran. It likely failed to load or wasn't available.",
  [ConsentStatus.NOT_APPLICABLE]: "No privacy notices apply to this asset",
};

export const DiscoveryErrorStatuses: ConsentStatus[] = [
  ConsentStatus.WITHOUT_CONSENT,
  ConsentStatus.PRE_CONSENT,
  ConsentStatus.CMP_ERROR,
];

export enum DiscoveredAssetsColumnKeys {
  NAME = "name",
  RESOURCE_TYPE = "resource_type",
  SYSTEM = "system",
  DATA_USES = "data_uses",
  LOCATIONS = "locations",
  DOMAIN = "domain",
  PAGE = "page",
  CONSENT_AGGREGATED = "consent_aggregated",
  ACTIONS = "actions",
}

export enum DiscoveredSystemAggregateColumnKeys {
  SYSTEM_NAME = "system_name",
  TOTAL_UPDATES = "total_updates",
  DATA_USE = "data_use",
  LOCATIONS = "locations",
  DOMAINS = "domains",
  ACTIONS = "actions",
}

export enum ConsentBreakdownColumnKeys {
  LOCATION = "location",
  PAGE = "page",
  STATUS = "status",
}

export const MONITOR_UPDATES_TO_IGNORE = [
  "classified_low_confidence",
  "classified_medium_confidence",
  "classified_high_confidence",
] as const satisfies readonly (
  | keyof DatastoreMonitorUpdates
  | keyof WebMonitorUpdates
)[];

export const MONITOR_UPDATE_NAMES = new Map<
  | keyof WebMonitorUpdates
  | keyof Omit<
      DatastoreMonitorUpdates,
      (typeof MONITOR_UPDATES_TO_IGNORE)[number]
    >,
  [string, string]
>([
  ["cookie", ["Cookie", "Cookies"]],
  ["browser_request", ["Browser request", "Browser requests"]],
  ["image", ["Image", "Images"]],
  ["iframe", ["iFrame", "iFrames"]],
  ["javascript_tag", ["JavaScript tag", "JavaScript tags"]],
  ["unlabeled", ["Unlabeled", "Unlabeled"]],
  ["in_review", ["Classified", "Classified"]],
  ["classifying", ["Classifying", "Classifying"]],
  ["removals", ["Removal", "Removals"]],
  ["reviewed", ["Reviewed", "Reviewed"]],
]);

export const MONITOR_UPDATE_ORDER = [
  "cookie",
  "image",
  "javascript_tag",
  "iframe",
  "browser_request",
  "unlabeled",
  "classifying",
  "in_review",
  "reviewed",
  "removals",
] as const satisfies readonly (
  | keyof DatastoreMonitorUpdates
  | keyof WebMonitorUpdates
)[];

export enum ConfidenceLevelLabel {
  HIGH = "High confidence",
  MEDIUM = "Medium confidence",
  LOW = "Low confidence",
}

export enum InfrastructureSystemBulkActionType {
  ADD = "add",
  IGNORE = "ignore",
  RESTORE = "restore",
}

export const INFRASTRUCTURE_SYSTEMS_TABS = [
  {
    key: ActionCenterTabHash.ATTENTION_REQUIRED,
    label: "Attention required",
  },
  {
    key: ActionCenterTabHash.ADDED,
    label: "Activity",
  },
  {
    key: ActionCenterTabHash.IGNORED,
    label: "Ignored",
  },
] as const;

export const INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS = {
  STATUS: "status-section",
  VENDOR: "vendor-section",
  DATA_USES: "data-uses-section",
} as const;

/**
 * Vendor filter options - hardcoded as per requirements
 */
export const VENDOR_FILTER_OPTIONS = [
  { key: "known", label: "Known vendors" },
  { key: "unknown", label: "Unknown vendors" },
] as const;

/**
 * Maps DiffStatus to display labels for infrastructure systems
 */
export const INFRASTRUCTURE_DIFF_STATUS_LABEL: Record<DiffStatus, string> = {
  [DiffStatus.ADDITION]: "New",
  [DiffStatus.CLASSIFICATION_ADDITION]: "Classified",
  [DiffStatus.CLASSIFICATION_UPDATE]: "Classified",
  [DiffStatus.REVIEWED]: "Reviewed",
  [DiffStatus.MONITORED]: "Approved",
  [DiffStatus.REMOVAL]: "Removed",
  [DiffStatus.MUTED]: "Ignored",
  [DiffStatus.CLASSIFICATION_QUEUED]: "Classifying",
  [DiffStatus.CLASSIFYING]: "Classifying",
  [DiffStatus.PROMOTING]: "Approving",
  [DiffStatus.REMOVING]: "Removing",
  [DiffStatus.CLASSIFICATION_ERROR]: "Error",
  [DiffStatus.PROMOTION_ERROR]: "Error",
  [DiffStatus.REMOVAL_PROMOTION_ERROR]: "Error",
};

/**
 * Maps DiffStatus to tag colors for infrastructure systems
 */
export const INFRASTRUCTURE_DIFF_STATUS_COLOR: Partial<
  Record<DiffStatus, CUSTOM_TAG_COLOR>
> = {
  [DiffStatus.ADDITION]: CUSTOM_TAG_COLOR.SUCCESS,
  [DiffStatus.REMOVAL]: CUSTOM_TAG_COLOR.ERROR,
  [DiffStatus.MONITORED]: CUSTOM_TAG_COLOR.DEFAULT,
  [DiffStatus.MUTED]: CUSTOM_TAG_COLOR.DEFAULT,
};
