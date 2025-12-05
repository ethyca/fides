import { DiffStatus } from "~/types/api";

export const INFRASTRUCTURE_SYSTEM_FILTERS = [
  "all",
  "new",
  "active",
  "inactive",
  "known",
  "unknown",
  "removed",
] as const;

export type InfrastructureSystemFilterLabel =
  (typeof INFRASTRUCTURE_SYSTEM_FILTERS)[number];

export const INFRASTRUCTURE_SYSTEM_FILTER_LABELS: Record<
  InfrastructureSystemFilterLabel,
  string
> = {
  all: "All Apps",
  new: "New Apps",
  active: "Active",
  inactive: "Inactive",
  known: "Known Vendors",
  unknown: "Unknown Vendors",
  removed: "Removed",
} as const;

export const INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS = {
  STATUS: "status-section",
  VENDOR: "vendor-section",
} as const;

/**
 * Maps infrastructure system filter labels to API parameters
 */
export const mapStatusFilterToDiffStatus = (
  filter: InfrastructureSystemFilterLabel,
): DiffStatus | null => {
  switch (filter) {
    case "new":
      return DiffStatus.ADDITION;
    case "removed":
      return DiffStatus.REMOVAL;
    default:
      return null;
  }
};

/**
 * Maps infrastructure system filter labels to status values for metadata
 */
export const mapStatusFilterToMetadataStatus = (
  filter: InfrastructureSystemFilterLabel,
): string | null => {
  switch (filter) {
    case "active":
      return "ACTIVE";
    case "inactive":
      return "INACTIVE";
    default:
      return null;
  }
};
