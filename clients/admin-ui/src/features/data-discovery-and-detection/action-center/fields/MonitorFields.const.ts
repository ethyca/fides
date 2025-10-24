import { CUSTOM_TAG_COLOR, Icons } from "fidesui";

import { DiffStatus, StagedResourceTypeValue } from "~/types/api";

export const TREE_PAGE_SIZE = 100;
export const TREE_NODE_LOAD_MORE_TEXT = "Load more...";
export const TREE_NODE_LOAD_MORE_KEY_PREFIX = "load_more";
export const TREE_NODE_SKELETON_KEY_PREFIX = "skeleton";

export const FIELD_PAGE_SIZE = 25;

export const RESOURCE_STATUS = [
  "Approved",
  "Classifying",
  "Confirmed",
  "Ignored",
  "In Review",
  "Removed",
  "Unlabeled",
] as const;

export type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];

export const DIFF_TO_RESOURCE_STATUS: Record<DiffStatus, ResourceStatusLabel> =
  {
    addition: "Unlabeled",
    approved: "Approved",
    classification_addition: "In Review",
    classification_queued: "Classifying",
    classification_update: "In Review",
    classifying: "Classifying",
    monitored: "Confirmed",
    muted: "Ignored",
    promoting: "In Review",
    removal: "Removed",
    removing: "In Review",
  } as const;

export const MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: CUSTOM_TAG_COLOR;
  }
> = {
  addition: { label: "Unlabeled" }, // No tag for this status
  approved: { label: "Approved", color: CUSTOM_TAG_COLOR.SUCCESS },
  classification_addition: {
    label: "In Review",
    color: CUSTOM_TAG_COLOR.CAUTION,
  },
  classification_queued: { label: "Classifying", color: CUSTOM_TAG_COLOR.INFO },
  classification_update: {
    label: "In Review",
    color: CUSTOM_TAG_COLOR.CAUTION,
  },
  classifying: { label: "Classifying", color: CUSTOM_TAG_COLOR.INFO },
  monitored: { label: "Confirmed", color: CUSTOM_TAG_COLOR.MINOS },
  muted: { label: "Ignored", color: CUSTOM_TAG_COLOR.DEFAULT },
  promoting: { label: "In Review", color: CUSTOM_TAG_COLOR.CAUTION },
  removal: { label: "Removed", color: CUSTOM_TAG_COLOR.ERROR },
  removing: { label: "In Review", color: CUSTOM_TAG_COLOR.CAUTION },
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
