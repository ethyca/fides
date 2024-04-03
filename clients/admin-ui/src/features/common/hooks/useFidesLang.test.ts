import useFidesLang from "./useFidesLang";
import ReactDomServer from "react-dom/server";

describe("Fides Language Helper Hook", () => {
  const {
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
  } = useFidesLang();

  describe("getDataUseDisplayName ", () => {
    it("returns just the data use name in bold if it's a top-level name", () => {
      expect(
        ReactDomServer.renderToStaticMarkup(getDataUseDisplayName("analytics"))
      ).toBe("<strong>Analytics</strong>");
    });
    it("returns the top-level parent name in bold and the name if it's a child data use", () => {
      expect(
        ReactDomServer.renderToStaticMarkup(
          getDataUseDisplayName("analytics.reporting")
        )
      ).toBe(
        "<span><strong>Analytics:</strong> Analytics for Reporting</span>"
      );
    });
    it("returns the key if it can't find the data use", () => {
      expect(getDataUseDisplayName("invalidkey")).toBe("invalidkey");
    });
  });

  describe("getDataCategoryDisplayName ", () => {
    it("returns just the data use name in bold if it's a top-level name", () => {
      expect(
        ReactDomServer.renderToStaticMarkup(
          getDataCategoryDisplayName("system")
        )
      ).toBe("<strong>System Data</strong>");
    });
    it("returns the top-level parent name in bold and the name if it's a child data category", () => {
      expect(
        ReactDomServer.renderToStaticMarkup(
          getDataCategoryDisplayName("system.authentication")
        )
      ).toBe("<span><strong>System Data:</strong> Authentication Data</span>");
    });
    it("returns the key if it can't find the data category", () => {
      expect(getDataCategoryDisplayName("invalidkey")).toBe("invalidkey");
    });
  });

  describe("getDataSubjectDisplayName ", () => {
    it("returns just the data use name without bold if it's a top-level name", () => {
      expect(
        ReactDomServer.renderToStaticMarkup(
          getDataSubjectDisplayName("citizen_voter")
        )
      ).toBe("Citizen Voter");
    });
    it("returns the key if it can't find the data category", () => {
      expect(getDataSubjectDisplayName("invalidkey")).toBe("invalidkey");
    });
  });
});

// Mock Data
jest.mock("~/features/data-use/data-use.slice", () => {
  return {
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
  };
});

jest.mock("~/features/taxonomy", () => {
  return {
    useGetAllDataCategoriesQuery: jest
      .fn()
      .mockReturnValue({ isLoading: false }),
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
    ]),
  };
});

jest.mock("~/features/data-subjects/data-subject.slice", () => {
  return {
    useGetAllDataSubjectsQuery: jest.fn().mockReturnValue({ isLoading: false }),
    selectDataSubjects: jest.fn().mockReturnValue([
      {
        fides_key: "citizen_voter",
        name: "Citizen Voter",
      },
    ]),
  };
});

jest.mock("~/app/hooks", () => {
  return {
    useAppSelector: jest.fn().mockImplementation((f) => f()),
  };
});
