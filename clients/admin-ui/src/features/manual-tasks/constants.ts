import { TaskStatus } from "./mocked/types";

export interface StatusMapEntry {
  color: string;
  label: string;
}

// Map task status to tag colors and labels - aligned with RequestStatusBadge colors
export const STATUS_MAP: Record<TaskStatus, StatusMapEntry> = {
  new: { color: "info", label: "New" },
  completed: { color: "success", label: "Completed" },
  skipped: { color: "marble", label: "Skipped" },
};

// Filter options for status column
export const STATUS_FILTER_OPTIONS = [
  { text: "New", value: "new" },
  { text: "Completed", value: "completed" },
  { text: "Skipped", value: "skipped" },
];

// Filter options for request type column
export const REQUEST_TYPE_FILTER_OPTIONS = [
  { text: "Access", value: "access" },
  { text: "Erasure", value: "erasure" },
];
