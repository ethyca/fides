import { MOCK_OKTA_APPS } from "~/mocks/data";

import { OKTA_APP_FILTER_TABS } from "../oktaAppFilters";

describe("Okta App Filters — predicates", () => {
  const cases = [
    {
      label: "new",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) => a.diff_status === "addition",
      expected: ["Salesforce"],
    },
    {
      label: "active",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) =>
        a.metadata?.status === "ACTIVE",
      expected: ["Salesforce"],
    },
    {
      label: "inactive",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) =>
        a.metadata?.status === "INACTIVE",
      expected: [],
    },
    {
      label: "known",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) => !!a.vendor_id,
      expected: ["Salesforce"],
    },
    {
      label: "unknown",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) => !a.vendor_id,
      expected: [],
    },
    {
      label: "removed",
      filter: (a: (typeof MOCK_OKTA_APPS)[0]) => a.diff_status === "removal",
      expected: [],
    },
  ];

  it.each(cases)(
    "filter $label returns expected items",
    ({ filter, expected }) => {
      expect(MOCK_OKTA_APPS.filter(filter).map((a) => a.name)).toEqual(
        expected,
      );
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
      expect(MOCK_OKTA_APPS.filter((a) => tab!.filter(a as any)).length).toBe(
        expected,
      );
    },
  );
});
