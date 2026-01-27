import { fireEvent, screen } from "@testing-library/react";
import React from "react";

// Mock query-string to avoid ESM import issue in Jest
jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));

import AssetReportingTable from "../../../src/features/asset-reporting/AssetReportingTable";
import { render } from "../../utils/test-utils";

// Mock the DebouncedSearchInput component
jest.mock("../../../src/features/common/DebouncedSearchInput", () => ({
  DebouncedSearchInput: ({
    value,
    onChange,
    placeholder,
    "data-testid": testId,
  }: {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    "data-testid"?: string;
  }) => (
    <input
      data-testid={testId || "debounced-search-input"}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  ),
}));

describe("AssetReportingTable", () => {
  const mockUpdateSearch = jest.fn();
  const mockColumns = [
    {
      title: "Asset name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Type",
      dataIndex: "asset_type",
      key: "asset_type",
    },
  ];

  const mockTableProps = {
    dataSource: [
      {
        id: "asset-1",
        name: "Test Cookie",
        asset_type: "Cookie",
      },
      {
        id: "asset-2",
        name: "Test Script",
        asset_type: "Javascript tag",
      },
    ],
    loading: false,
    rowKey: "id",
    pagination: {
      current: 1,
      pageSize: 25,
      total: 2,
    },
  };

  const defaultProps = {
    columns: mockColumns as any,
    searchQuery: "",
    updateSearch: mockUpdateSearch,
    tableProps: mockTableProps as any,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the search input", () => {
    render(<AssetReportingTable {...defaultProps} />);

    const searchInput = screen.getByTestId("asset-search-input");
    expect(searchInput).toBeInTheDocument();
  });

  it("renders the table", () => {
    render(<AssetReportingTable {...defaultProps} />);

    const table = screen.getByTestId("asset-reporting-table");
    expect(table).toBeInTheDocument();
  });

  it("displays the search placeholder text", () => {
    render(<AssetReportingTable {...defaultProps} />);

    const searchInput = screen.getByTestId("asset-search-input");
    expect(searchInput).toHaveAttribute(
      "placeholder",
      "Search by asset name or domain...",
    );
  });

  it("passes searchQuery value to search input", () => {
    render(<AssetReportingTable {...defaultProps} searchQuery="test query" />);

    const searchInput = screen.getByTestId("asset-search-input");
    expect(searchInput).toHaveValue("test query");
  });

  it("calls updateSearch when search input changes", () => {
    render(<AssetReportingTable {...defaultProps} />);

    const searchInput = screen.getByTestId("asset-search-input");
    fireEvent.change(searchInput, { target: { value: "cookie" } });

    expect(mockUpdateSearch).toHaveBeenCalledWith("cookie");
  });

  it("handles undefined searchQuery gracefully", () => {
    render(<AssetReportingTable {...defaultProps} searchQuery={undefined} />);

    const searchInput = screen.getByTestId("asset-search-input");
    expect(searchInput).toHaveValue("");
  });

  it("renders table with correct data-testid", () => {
    render(<AssetReportingTable {...defaultProps} />);

    expect(screen.getByTestId("asset-reporting-table")).toBeInTheDocument();
  });
});
