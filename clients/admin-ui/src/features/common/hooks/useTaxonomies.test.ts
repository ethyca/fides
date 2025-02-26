/**
 * // For `renderToStaticMarkup` to work, we need to be in `node` env
 * @jest-environment node
 */

import { renderToStaticMarkup } from "react-dom/server";

import useTaxonomies from "./useTaxonomies";

describe("Fides Language Helper Hook", () => {
  const {
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
  } = useTaxonomies();

  describe("getDataUseDisplayName ", () => {
    it("returns just the data use name in bold if it's a top-level name", () => {
      expect(renderToStaticMarkup(getDataUseDisplayName("analytics"))).toBe(
        "<strong>Analytics</strong>",
      );
    });
    it("returns the top-level parent name in bold and the name if it's a child data use", () => {
      expect(
        renderToStaticMarkup(getDataUseDisplayName("analytics.reporting")),
      ).toBe("<strong>Analytics:</strong> Analytics for Reporting");
    });
    it("returns the key if it can't find the data use", () => {
      expect(getDataUseDisplayName("invalidkey")).toBe("invalidkey");
    });
  });

  describe("getDataCategoryDisplayName ", () => {
    it("returns just the data use name in bold if it's a top-level or secondary-level name", () => {
      expect(renderToStaticMarkup(getDataCategoryDisplayName("system"))).toBe(
        "<strong>System Data</strong>",
      );
      expect(
        renderToStaticMarkup(
          getDataCategoryDisplayName("system.authentication"),
        ),
      ).toBe("<strong>Authentication Data</strong>");
    });
    it("returns the top-level parent name in bold and the name if it's a child data category", () => {
      expect(
        renderToStaticMarkup(
          getDataCategoryDisplayName("system.authentication.user"),
        ),
      ).toBe("<strong>Authentication Data:</strong> User");
    });
    it("returns the key if it can't find the data category", () => {
      expect(getDataCategoryDisplayName("invalidkey")).toBe("invalidkey");
    });
  });

  describe("getDataSubjectDisplayName ", () => {
    it("returns just the data use name without bold if it's a top-level name", () => {
      expect(
        renderToStaticMarkup(getDataSubjectDisplayName("citizen_voter")),
      ).toBe("Citizen Voter");
    });
    it("returns the key if it can't find the data category", () => {
      expect(getDataSubjectDisplayName("invalidkey")).toBe("invalidkey");
    });
  });
});

// Mock Data
jest.mock("~/features/data-use/data-use.slice", () => ({
  useGetAllDataUsesQuery: jest.fn().mockReturnValue({ isLoading: false }),
  selectDataUses: jest.fn().mockReturnValue([
    {
      fides_key: "analytics",
      name: "Analytics",
      parent_key: null,
    },
    {
      fides_key: "analytics.reporting",
      name: "Analytics for Reporting",
      parent_key: "analytics",
    },
  ]),
}));

jest.mock("~/features/taxonomy", () => ({
  useGetAllDataCategoriesQuery: jest.fn().mockReturnValue({ isLoading: false }),
  selectDataCategories: jest.fn().mockReturnValue([
    {
      fides_key: "system",
      name: "System Data",
      parent_key: null,
    },
    {
      fides_key: "system.authentication",
      name: "Authentication Data",
      parent_key: "system",
    },
    {
      fides_key: "system.authentication.user",
      name: "User",
      parent_key: "system.authentication",
    },
  ]),
}));

jest.mock("~/features/data-subjects/data-subject.slice", () => ({
  useGetAllDataSubjectsQuery: jest.fn().mockReturnValue({ isLoading: false }),
  selectDataSubjects: jest.fn().mockReturnValue([
    {
      fides_key: "citizen_voter",
      name: "Citizen Voter",
    },
  ]),
}));

jest.mock("~/app/hooks", () => ({
  useAppSelector: jest.fn().mockImplementation((f) => f()),
}));
