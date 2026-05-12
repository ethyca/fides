import { CUSTOM_TAG_COLOR, Icons } from "fidesui";

import { DiffStatus, StagedResourceTypeValue, StatusCounts } from "~/types/api";

export const TREE_PAGE_SIZE = 100;
export const TREE_NODE_LOAD_MORE_TEXT = "Load more...";
export const TREE_NODE_LOAD_MORE_KEY_PREFIX = "load_more";
export const TREE_NODE_SKELETON_KEY_PREFIX = "skeleton";

export const FIELD_PAGE_SIZE = 25;

export const RESOURCE_STATUS = [
  "Unlabeled",
  "Classifying",
  "Classified",
  "Reviewed",
  "Approving",
  "Approved",
  "Removed",
  "Ignored",
  "Error",
  "Removing",
] as const;

export type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];

// Statuses to exclude from filters by default
export const EXCLUDED_FILTER_STATUSES: ResourceStatusLabel[] = [
  "Approved",
  "Ignored",
  "Approving",
  "Removing",
];

export const DEFAULT_FILTER_STATUSES: Exclude<
  ResourceStatusLabel,
  "Approved" | "Ignored" | "Approving" | "Removing"
>[] = [
  "Unlabeled",
  "Classifying",
  "Classified",
  "Reviewed",
  "Removed",
  "Error",
];

export const STATUS_COUNTS: Record<keyof StatusCounts, keyof StatusCounts> = {
  addition: "addition",
  reviewed: "reviewed",
  classified: "classifying",
  classifying: "classifying",
  monitored: "monitored",
  removal: "removal",
} as const;

export const STATUS_COUNTS_TO_RESOURCE_STATUS: Record<
  keyof StatusCounts,
  ResourceStatusLabel
> = {
  addition: "Unlabeled",
  reviewed: "Reviewed",
  classified: "Classified",
  classifying: "Classifying",
  monitored: "Approved",
  removal: "Removed",
} as const;

export const DIFF_TO_RESOURCE_STATUS: Record<DiffStatus, ResourceStatusLabel> =
  {
    addition: "Unlabeled",
    reviewed: "Reviewed",
    classification_addition: "Classified",
    classification_error: "Error",
    classification_queued: "Classifying",
    classification_update: "Classified",
    classifying: "Classifying",
    monitored: "Approved",
    muted: "Ignored",
    promoting: "Approving",
    promotion_error: "Error",
    removal: "Removed",
    removing: "Removing",
    removal_promotion_error: "Error",
  } as const;

export const MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: CUSTOM_TAG_COLOR;
  }
> = {
  addition: { label: "Unlabeled" }, // No tag for this status
  reviewed: { label: "Reviewed", color: CUSTOM_TAG_COLOR.ALERT },
  classification_addition: {
    label: "Classified",
    color: CUSTOM_TAG_COLOR.CAUTION,
  },
  classification_error: {
    label: "Error",
    color: CUSTOM_TAG_COLOR.ERROR,
  },
  classification_queued: {
    label: "Classifying",
    color: CUSTOM_TAG_COLOR.INFO,
  },
  classification_update: {
    label: "Classified",
    color: CUSTOM_TAG_COLOR.CAUTION,
  },
  classifying: { label: "Classifying", color: CUSTOM_TAG_COLOR.INFO },
  monitored: { label: "Approved", color: CUSTOM_TAG_COLOR.SUCCESS },
  muted: { label: "Ignored", color: CUSTOM_TAG_COLOR.DEFAULT },
  promoting: { label: "Approving", color: CUSTOM_TAG_COLOR.DEFAULT },
  promotion_error: {
    label: "Error",
    color: CUSTOM_TAG_COLOR.ERROR,
  },
  removal: { label: "Removed", color: CUSTOM_TAG_COLOR.ERROR },
  removing: { label: "Removing", color: CUSTOM_TAG_COLOR.DEFAULT },
  removal_promotion_error: {
    label: "Error",
    color: CUSTOM_TAG_COLOR.ERROR,
  },
} as const;

// Map resource type to icon
export const MAP_DATASTORE_RESOURCE_TYPE_TO_ICON: Partial<
  Record<StagedResourceTypeValue, Icons.CarbonIconType>
> = {
  [StagedResourceTypeValue.DATABASE]: Icons.Layers,
  [StagedResourceTypeValue.FIELD]: Icons.Column,
  [StagedResourceTypeValue.SCHEMA]: Icons.Db2Database,
  [StagedResourceTypeValue.TABLE]: Icons.Table,
} as const;

// Map tree resource change indicator to status info
export const MAP_DIFF_STATUS_TO_STATUS_INFO: Partial<
  Record<
    DiffStatus,
    {
      color: string;
      tooltip: string;
    }
  >
> = {
  [DiffStatus.ADDITION]: {
    color: "var(--fidesui-color-success)",
    tooltip: "This resource was added in the latest scan",
  },
  [DiffStatus.REMOVAL]: {
    color: "var(--fidesui-color-error)",
    tooltip: "This resource was removed in the latest scan",
  },
} as const;
