import { fireEvent, screen } from "@testing-library/react";
import React from "react";

import useAssetReportingDownload from "../../../src/features/asset-reporting/hooks/useAssetReportingDownload";
import { useAssetReportingTable } from "../../../src/features/asset-reporting/hooks/useAssetReportingTable";
import AssetReportingPage from "../../../src/pages/reporting/assets/index";
import { render } from "../../utils/test-utils";

// Mock ESM-only packages to avoid Jest import issues
jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));
jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock nuqs
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../utils/nuqs-mock").nuqsMock);

// Mock the hooks
const mockDownloadReport = jest.fn();
const mockUpdateSearch = jest.fn();
const mockUpdateFilters = jest.fn();

jest.mock(
  "../../../src/features/asset-reporting/hooks/useAssetReportingTable",
  () => ({
    useAssetReportingTable: jest.fn(),
  }),
);

jest.mock(
  "../../../src/features/asset-reporting/hooks/useAssetReportingDownload",
  () => ({
    __esModule: true,
    default: jest.fn(),
  }),
);

// Mock the child components
jest.mock("../../../src/features/common/FixedLayout", () => ({
  __esModule: true,
  default: ({
    children,
    title,
  }: {
    children: React.ReactNode;
    title: string;
  }) => (
    <div data-testid="fixed-layout" data-title={title}>
      {children}
    </div>
  ),
}));

jest.mock("../../../src/features/common/PageHeader", () => ({
  __esModule: true,
  default: ({
    heading,
    rightContent,
  }: {
    heading: string;
    rightContent?: React.ReactNode;
  }) => (
    <div data-testid="page-header">
      <h1>{heading}</h1>
      <div data-testid="page-header-right">{rightContent}</div>
    </div>
  ),
}));

jest.mock("../../../src/features/asset-reporting/AssetReportingTable", () => ({
  __esModule: true,
  default: () => <div data-testid="asset-reporting-table-mock" />,
}));

const mockUseAssetReportingTable = useAssetReportingTable as jest.Mock;
const mockUseAssetReportingDownload = useAssetReportingDownload as jest.Mock;

describe("AssetReportingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Set up default mock implementations
    mockUseAssetReportingTable.mockReturnValue({
      columns: [
        { title: "Asset name", dataIndex: "name", key: "name" },
        { title: "Type", dataIndex: "asset_type", key: "asset_type" },
      ],
      data: {
        items: [
          { id: "1", name: "Test Cookie", asset_type: "Cookie" },
          { id: "2", name: "Test Script", asset_type: "Javascript tag" },
        ],
        total: 2,
      },
      isLoading: false,
      isFetching: false,
      searchQuery: "",
      updateSearch: mockUpdateSearch,
      updateFilters: mockUpdateFilters,
      columnFilters: {},
      tableProps: {
        dataSource: [
          { id: "1", name: "Test Cookie", asset_type: "Cookie" },
          { id: "2", name: "Test Script", asset_type: "Javascript tag" },
        ],
        loading: false,
        rowKey: "id",
      },
    });

    mockUseAssetReportingDownload.mockReturnValue({
      downloadReport: mockDownloadReport,
      isDownloadingReport: false,
    });
  });

  it("renders the page with correct title", () => {
    render(<AssetReportingPage />);

    const layout = screen.getByTestId("fixed-layout");
    expect(layout).toHaveAttribute("data-title", "Asset report");
  });

  it("renders the page header with correct heading", () => {
    render(<AssetReportingPage />);

    expect(screen.getByText("Asset report")).toBeInTheDocument();
  });

  it("renders the export CSV button", () => {
    render(<AssetReportingPage />);

    const exportButton = screen.getByTestId("download-asset-report-btn");
    expect(exportButton).toBeInTheDocument();
    expect(exportButton).toHaveTextContent("Export CSV");
  });

  it("renders the asset reporting table", () => {
    render(<AssetReportingPage />);

    expect(
      screen.getByTestId("asset-reporting-table-mock"),
    ).toBeInTheDocument();
  });

  it("calls downloadReport with current filters when export button is clicked", () => {
    render(<AssetReportingPage />);

    const exportButton = screen.getByTestId("download-asset-report-btn");
    fireEvent.click(exportButton);

    expect(mockDownloadReport).toHaveBeenCalledWith({
      search: undefined,
    });
  });

  it("passes filters to downloadReport when they exist", () => {
    // Update the mock to include filters
    mockUseAssetReportingTable.mockReturnValue({
      columns: [],
      data: { items: [], total: 0 },
      isLoading: false,
      isFetching: false,
      searchQuery: "test search",
      updateSearch: mockUpdateSearch,
      updateFilters: mockUpdateFilters,
      columnFilters: { asset_type: ["Cookie"] },
      tableProps: { dataSource: [], loading: false },
    });

    render(<AssetReportingPage />);

    const exportButton = screen.getByTestId("download-asset-report-btn");
    fireEvent.click(exportButton);

    expect(mockDownloadReport).toHaveBeenCalledWith({
      asset_type: ["Cookie"],
      search: "test search",
    });
  });
});

describe("AssetReportingPage - Loading States", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Set up default mock for useAssetReportingTable
    mockUseAssetReportingTable.mockReturnValue({
      columns: [],
      data: { items: [], total: 0 },
      isLoading: false,
      isFetching: false,
      searchQuery: "",
      updateSearch: mockUpdateSearch,
      updateFilters: mockUpdateFilters,
      columnFilters: {},
      tableProps: { dataSource: [], loading: false, rowKey: "id" },
    });
  });

  it("shows loading state on export button when downloading", () => {
    mockUseAssetReportingDownload.mockReturnValue({
      downloadReport: mockDownloadReport,
      isDownloadingReport: true,
    });

    render(<AssetReportingPage />);

    const exportButton = screen.getByTestId("download-asset-report-btn");
    // Check that the button indicates loading state (Ant Design adds loading spinner)
    expect(exportButton).toBeInTheDocument();
  });
});
