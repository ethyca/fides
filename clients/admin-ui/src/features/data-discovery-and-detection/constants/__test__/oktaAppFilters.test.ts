import { oktaStubClient } from "~/features/data-discovery-and-detection/action-center/utils/oktaStubClient";
import { StagedResourceAPIResponse } from "~/types/api";

import { OKTA_APP_FILTER_TABS } from "../oktaAppFilters";

describe("Okta App Filters — predicates", () => {
  const mockApps = oktaStubClient.getAllMockApps();

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
      const mockApps = oktaStubClient.getAllMockApps();
      expect(mockApps.filter((a) => tab!.filter(a as any)).length).toBe(
        expected,
      );
    },
  );
});
