import { StagedResourceAPIResponse } from "~/types/api";
import { ApplicationStatus } from "~/types/api/models/ApplicationStatus";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import { OKTA_APP_FILTER_TABS } from "../oktaAppFilters";

// Mock data for testing filters
const mockApps: (StagedResourceAPIResponse & {
  diff_status?: string;
})[] = [
  {
    urn: "urn:okta:app:12345678-1234-1234-1234-123456789012",
    name: "Salesforce",
    diff_status: DiffStatus.ADDITION,
    metadata: {
      status: ApplicationStatus.ACTIVE,
    },
    vendor_id: "fds.1234",
  },
];

describe("Okta App Filters — predicates", () => {

  const cases = [
    {
      label: "new",
      filter: (a: StagedResourceAPIResponse) => a.diff_status === "addition",
      expected: ["Salesforce"],
    },
    {
      label: "active",
      filter: (a: StagedResourceAPIResponse) => a.metadata?.status === "ACTIVE",
      expected: ["Salesforce"],
    },
    {
      label: "inactive",
      filter: (a: StagedResourceAPIResponse) =>
        a.metadata?.status === "INACTIVE",
      expected: [],
    },
    {
      label: "known",
      filter: (a: StagedResourceAPIResponse) => !!a.vendor_id,
      expected: ["Salesforce"],
    },
    {
      label: "unknown",
      filter: (a: StagedResourceAPIResponse) => !a.vendor_id,
      expected: [],
    },
    {
      label: "removed",
      filter: (a: StagedResourceAPIResponse) => a.diff_status === "removal",
      expected: [],
    },
  ];

  it.each(cases)(
    "filter $label returns expected items",
    ({ filter, expected }) => {
      expect(
        mockApps
          .filter((a) => filter(a as StagedResourceAPIResponse))
          .map((a) => a.name),
      ).toEqual(expected);
    },
  );
});

describe("Okta App Filters — tabs config", () => {
  const expectedCounts = {
    all: 1,
    new: 1,
    active: 1,
    inactive: 0,
    known: 1,
    unknown: 0,
    removed: 0,
  };

  it.each(Object.entries(expectedCounts))(
    "tab '%s' shows count %d",
    (value, expected) => {
      const tab = OKTA_APP_FILTER_TABS.find((t) => t.value === value);
      expect(mockApps.filter((a) => tab!.filter(a as any)).length).toBe(
        expected,
      );
    },
  );
});
