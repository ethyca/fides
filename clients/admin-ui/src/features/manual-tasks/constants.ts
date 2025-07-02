import { ManualFieldRequestType, ManualFieldStatus } from "~/types/api";

export interface StatusMapEntry {
  color: string;
  label: string;
}

// Map task status to tag colors and labels - aligned with RequestStatusBadge colors
export const STATUS_MAP: Record<ManualFieldStatus, StatusMapEntry> = {
  [ManualFieldStatus.NEW]: { color: "info", label: "New" },
  [ManualFieldStatus.COMPLETED]: { color: "success", label: "Completed" },
  [ManualFieldStatus.SKIPPED]: { color: "marble", label: "Skipped" },
};

// Filter options for status column
export const STATUS_FILTER_OPTIONS = [
  { text: "New", value: ManualFieldStatus.NEW },
  { text: "Completed", value: ManualFieldStatus.COMPLETED },
  { text: "Skipped", value: ManualFieldStatus.SKIPPED },
];

// Filter options for request type column
export const REQUEST_TYPE_FILTER_OPTIONS = [
  { text: "Access", value: ManualFieldRequestType.ACCESS },
  { text: "Erasure", value: ManualFieldRequestType.ERASURE },
];
