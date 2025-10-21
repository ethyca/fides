import { DiffStatus } from "~/types/api";

import { ResourceStatusLabel, ResourceStatusLabelColor } from "./types";

export const TREE_PAGE_SIZE = 100;
export const TREE_NODE_LOAD_MORE_TEXT = "Load more...";
export const TREE_NODE_LOAD_MORE_KEY_PREFIX = "load_more";
export const TREE_NODE_SKELETON_KEY_PREFIX = "skeleton";

export const FIELD_PAGE_SIZE = 25;

export const RESOURCE_STATUS = [
  "Attention Required",
  "In Review",
  "Classifying",
  "Approved",
  "Unmonitored",
  "Confirmed",
  "Removed",
] as const;

export const MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: ResourceStatusLabelColor;
  }
> = {
  classifying: { label: "Classifying", color: "blue" },
  classification_queued: { label: "Classifying", color: "blue" },
  classification_update: { label: "In Review", color: "nectar" },
  classification_addition: { label: "In Review", color: "blue" },
  addition: { label: "Attention Required", color: "blue" },
  muted: { label: "Unmonitored", color: "nectar" },
  removal: { label: "Removed", color: "red" },
  removing: { label: "In Review", color: "nectar" },
  promoting: { label: "In Review", color: "nectar" },
  monitored: { label: "Confirmed", color: "nectar" },
  approved: { label: "Approved", color: "green" },
} as const;
