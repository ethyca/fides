import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../../utils/nuqs-mock").nuqsMock);

// Mock the RTK Query hooks
jest.mock(
  "../../../../src/features/asset-reporting/asset-reporting.slice",
  () => ({
    useGetAllAssetsQuery: jest.fn(() => ({
      data: {
        items: [
          {
            id: "asset-1",
            name: "Test Cookie",
            asset_type: "Cookie",
            domain: "example.com",
            system_id: "system-1",
            system_name: "Test System",
            consent_status: "WITH_CONSENT",
            data_uses: ["analytics"],
            locations: ["us_ca"],
          },
          {
            id: "asset-2",
            name: "Test Script",
            asset_type: "Javascript tag",
            domain: "cdn.example.com",
            system_id: "system-1",
            system_name: "Test System",
            consent_status: "WITHOUT_CONSENT",
            data_uses: ["marketing.advertising"],
            locations: ["us_ny", "eu_de"],
          },
        ],
        total: 2,
        page: 1,
        size: 25,
        pages: 1,
      },
      isLoading: false,
      isFetching: false,
    })),
    useGetAssetReportingFilterOptionsQuery: jest.fn(() => ({
      data: {
        asset_type: ["Cookie", "Javascript tag"],
        consent_status: ["WITH_CONSENT", "WITHOUT_CONSENT"],
        system_id: ["system-1"],
        data_uses: ["analytics", "marketing.advertising"],
        locations: null, // Set to null to avoid iso function calls in tests
      },
      isLoading: false,
      isFetching: false,
    })),
  }),
);

// Mock useFeatures hook
const mockUseFeatures = jest.fn(() => ({
  flags: { assetConsentStatusLabels: true },
}));
jest.mock("../../../../src/features/common/features/features.slice", () => ({
  useFeatures: () => mockUseFeatures(),
}));

// Mock useTaxonomies hook
const mockDataUses = [
  { fides_key: "analytics", name: "Analytics" },
  { fides_key: "marketing.advertising", name: "Advertising" },
];
jest.mock("../../../../src/features/common/hooks/useTaxonomies", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    getDataUses: jest.fn(() => mockDataUses),
    getDataUseByKey: jest.fn((key: string) =>
      mockDataUses.find((du) => du.fides_key === key),
    ),
    getDataUseDisplayName: jest.fn((key: string) => {
      const displayNames: Record<string, string> = {
        analytics: "Analytics",
        "marketing.advertising": "Advertising",
      };
      return displayNames[key] || key;
    }),
  })),
}));

// Import after mocks so the mocked modules are used
// eslint-disable-next-line import/first
import { useAssetReportingTable } from "../../../../src/features/asset-reporting/hooks/useAssetReportingTable";
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
};

describe("useAssetReportingTable", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    nuqsTestHelpers.reset();
  });

  it("returns table state and columns", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    // Check that columns are defined
    expect(result.current.columns).toBeDefined();
    expect(Array.isArray(result.current.columns)).toBe(true);
    expect(result.current.columns.length).toBeGreaterThan(0);

    // Check that table props are defined
    expect(result.current.tableProps).toBeDefined();

    // Check that state management functions exist
    expect(typeof result.current.updateSearch).toBe("function");
    expect(typeof result.current.updateFilters).toBe("function");
    expect(typeof result.current.updateSorting).toBe("function");
    expect(typeof result.current.resetState).toBe("function");
  });

  it("returns data from the API", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
  });

  it("returns loading states", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it("has correct column definitions when consent status flag is enabled", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    const columnKeys = result.current.columns.map((col) => col.key);

    // Verify expected columns exist
    expect(columnKeys).toContain("name");
    expect(columnKeys).toContain("asset_type");
    expect(columnKeys).toContain("system_name");
    expect(columnKeys).toContain("consent_status");
    expect(columnKeys).toContain("data_uses");
    expect(columnKeys).toContain("domain");
    expect(columnKeys).toContain("locations");
  });

  it("excludes consent_status column when flag is disabled", () => {
    mockUseFeatures.mockReturnValue({
      flags: { assetConsentStatusLabels: false },
    });

    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    const columnKeys = result.current.columns.map((col) => col.key);

    expect(columnKeys).not.toContain("consent_status");
    expect(columnKeys).toContain("name");
    expect(columnKeys).toContain("data_uses");
  });

  it("exposes columnFilters for export functionality", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    // Initially empty
    expect(result.current.columnFilters).toEqual({});

    // Verify updateFilters function exists and can be called
    expect(typeof result.current.updateFilters).toBe("function");
    expect(() => {
      act(() => result.current.updateFilters({ asset_type: ["Cookie"] }));
    }).not.toThrow();
  });

  it("updateSearch function exists and can be called", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    expect(typeof result.current.updateSearch).toBe("function");
    expect(() => {
      act(() => result.current.updateSearch("test search"));
    }).not.toThrow();
  });

  it("resetState function exists and can be called", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    expect(typeof result.current.resetState).toBe("function");

    // Verify all state management functions can be called without throwing
    expect(() => {
      act(() => result.current.updateSearch("test"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateFilters({ asset_type: ["Cookie"] }));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.resetState());
    }).not.toThrow();
  });

  it("columns include filter configurations for filterable columns", () => {
    mockUseFeatures.mockReturnValue({
      flags: { assetConsentStatusLabels: true },
    });

    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    // Find the asset_type column
    const assetTypeColumn = result.current.columns.find(
      (col) => col.key === "asset_type",
    );
    expect(assetTypeColumn).toBeDefined();
    expect(assetTypeColumn?.filters).toBeDefined();
    expect(Array.isArray(assetTypeColumn?.filters)).toBe(true);

    // Find the consent_status column
    const consentStatusColumn = result.current.columns.find(
      (col) => col.key === "consent_status",
    );
    expect(consentStatusColumn).toBeDefined();
    expect(consentStatusColumn?.filters).toBeDefined();

    // Find the data_uses column
    const dataUsesColumn = result.current.columns.find(
      (col) => col.key === "data_uses",
    );
    expect(dataUsesColumn).toBeDefined();
    expect(dataUsesColumn?.filters).toBeDefined();
  });

  it("name column is sortable and fixed to left", () => {
    const { result } = renderHook(() =>
      useAssetReportingTable({ filters: {} }),
    );

    const nameColumn = result.current.columns.find((col) => col.key === "name");
    expect(nameColumn).toBeDefined();
    expect(nameColumn?.sorter).toBe(true);
    expect(nameColumn?.fixed).toBe("left");
  });
});
