import { DiffStatus, StagedResourceAPIResponse } from "~/types/api";
import { ApplicationStatus } from "~/types/api/models/ApplicationStatus";

export interface OktaAppFilterTab {
  label: string;
  value: string;
  count: number | null;
  filter: (resource: StagedResourceAPIResponse) => boolean;
}

export const OKTA_APP_FILTER_TABS: OktaAppFilterTab[] = [
  {
    label: "All Apps",
    value: "all",
    count: null,
    filter: () => true,
  },
  {
    label: "New Apps",
    value: "new",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.diff_status === DiffStatus.ADDITION,
  },
  {
    label: "Active",
    value: "active",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.metadata?.status === ApplicationStatus.ACTIVE,
  },
  {
    label: "Inactive",
    value: "inactive",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.metadata?.status === ApplicationStatus.INACTIVE,
  },
  {
    label: "Known Vendors",
    value: "known",
    count: null,
    filter: (resource: StagedResourceAPIResponse) => !!resource.vendor_id,
  },
  {
    label: "Unknown Vendors",
    value: "unknown",
    count: null,
    filter: (resource: StagedResourceAPIResponse) => !resource.vendor_id,
  },
  {
    label: "Removed",
    value: "removed",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.diff_status === DiffStatus.REMOVAL,
  },
];
