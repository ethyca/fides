import { StagedResourceAPIResponse } from "~/types/api";

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
      resource.diff_status === "addition",
  },
  {
    label: "Active",
    value: "active",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.metadata?.status === "ACTIVE",
  },
  {
    label: "Inactive",
    value: "inactive",
    count: null,
    filter: (resource: StagedResourceAPIResponse) =>
      resource.metadata?.status === "INACTIVE",
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
      resource.diff_status === "removal",
  },
];
