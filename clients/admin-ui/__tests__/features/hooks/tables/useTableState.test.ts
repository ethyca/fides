import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../../utils/nuqs-mock").nuqsMock);

// Mock localStorage for useLocalStorage hook
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { useTableState } from "../../../../src/features/common/table/hooks";
// Import the test helpers type and access from the mocked module
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
};

type SortKey = "name" | "createdAt" | "title";

describe("useTableState", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
    localStorageMock.clear();
  });

  it("manages table state with custom configuration", () => {
    const onStateChange = jest.fn();
    const { result } = renderHook(() =>
      useTableState<SortKey>({
        tableId: "test-table",
        pagination: {
          defaultPageSize: 30,
          pageSizeOptions: [10, 20, 30],
          showSizeChanger: false,
        },
        sorting: {
          defaultSortKey: "name",
          defaultSortOrder: "ascend",
        },
        onStateChange,
      }),
    );

    // Initial state reflects configuration defaults
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(30);
    expect(result.current.sortKey).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");
    expect(result.current.columnFilters).toEqual({});
    expect(result.current.searchQuery).toBeUndefined();
    expect(result.current.columnWidths).toEqual({});
    expect(result.current.paginationConfig).toEqual({
      pageSizeOptions: [10, 20, 30],
      showSizeChanger: false,
    });

    // Test that update functions exist and are callable (detailed behavior tested in separate hooks)
    expect(typeof result.current.updateSorting).toBe("function");
    expect(typeof result.current.updateFilters).toBe("function");
    expect(typeof result.current.updateSearch).toBe("function");
    expect(typeof result.current.updatePageIndex).toBe("function");
    expect(typeof result.current.updatePageSize).toBe("function");
    expect(typeof result.current.updateColumnWidth).toBe("function");
    expect(typeof result.current.resetColumnWidths).toBe("function");
    expect(typeof result.current.resetState).toBe("function");

    // Test that functions execute without errors
    expect(() => {
      act(() => result.current.updateSorting("createdAt", "descend"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateFilters({ status: ["active"] }));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateSearch("query"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateColumnWidth("name", 150));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.resetColumnWidths());
    }).not.toThrow();

    expect(() => {
      act(() => result.current.resetState());
    }).not.toThrow();

    // onStateChange called with updated state
    expect(onStateChange).toHaveBeenCalled();
  });

  it("reads state from URL correctly", () => {
    // Seed URL state with meaningful values (not empty strings that would be treated as falsy)
    nuqsTestHelpers.reset({
      page: 3,
      size: 10,
      sortKey: "name",
      sortOrder: "ascend",
      filters: { role: ["admin"] }, // Remove null values as they get filtered out
      search: "abc",
    });

    const { result } = renderHook(() =>
      useTableState<SortKey>({
        tableId: "test-table",
        pagination: { defaultPageSize: 25 },
        sorting: {
          defaultSortKey: "createdAt",
          defaultSortOrder: "descend",
        },
      }),
    );

    // Current state reflects URL values
    expect(result.current.pageIndex).toBe(3);
    expect(result.current.pageSize).toBe(10);
    expect(result.current.sortKey).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");
    expect(result.current.columnFilters).toEqual({
      role: ["admin"],
    });
    expect(result.current.searchQuery).toBe("abc");

    // Verify functions are available and executable
    expect(typeof result.current.updateSorting).toBe("function");
    expect(typeof result.current.updateFilters).toBe("function");
    expect(typeof result.current.updateSearch).toBe("function");
    expect(typeof result.current.updatePageIndex).toBe("function");
    expect(typeof result.current.updatePageSize).toBe("function");
    expect(typeof result.current.updateColumnWidth).toBe("function");
    expect(typeof result.current.resetColumnWidths).toBe("function");
    expect(typeof result.current.resetState).toBe("function");

    // Test some URL updates work (detailed behavior tested in individual hook tests)
    expect(() => {
      act(() => result.current.updateSorting("title", "descend"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateFilters({ role: ["user"] }));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateSearch("find me"));
    }).not.toThrow();
  });

  it("handles empty/default URL values correctly", () => {
    // Seed URL state with empty string values and null values from parsers
    nuqsTestHelpers.reset({
      page: 1,
      size: 25,
      sortKey: "", // Empty string from parser default
      sortOrder: null, // null from parseAsStringLiteral when not set
      filters: {},
      search: "", // Empty string from parser default
    });

    const { result } = renderHook(() =>
      useTableState<SortKey>({
        tableId: "test-table",
        pagination: { defaultPageSize: 25 },
        sorting: {
          defaultSortKey: "createdAt",
          defaultSortOrder: "descend",
        },
      }),
    );

    // Should fall back to configured defaults when URL has empty strings/null values
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(25);
    expect(result.current.sortKey).toBe("createdAt"); // Falls back to default because "" is falsy
    expect(result.current.sortOrder).toBe("descend"); // Falls back to default because null with ?? operator
    expect(result.current.columnFilters).toEqual({});
    expect(result.current.searchQuery).toBeUndefined(); // Empty string from URL is converted to undefined
    expect(result.current.columnWidths).toEqual({}); // Column widths start empty from localStorage
  });

  it("manages column widths with localStorage", () => {
    const { result } = renderHook(() =>
      useTableState<SortKey>({
        tableId: "test-table",
      }),
    );

    // Initial column widths should be empty
    expect(result.current.columnWidths).toEqual({});

    // Update a column width
    act(() => {
      result.current.updateColumnWidth("name", 150);
    });

    // Column width should be updated
    expect(result.current.columnWidths).toEqual({ name: 150 });

    // Update another column width
    act(() => {
      result.current.updateColumnWidth("createdAt", 200);
    });

    // Both column widths should be present
    expect(result.current.columnWidths).toEqual({ name: 150, createdAt: 200 });

    // Reset column widths
    act(() => {
      result.current.resetColumnWidths();
    });

    // Column widths should be empty again
    expect(result.current.columnWidths).toEqual({});

    // Verify localStorage was called
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "test-table:column-widths",
      JSON.stringify({ name: 150 }),
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "test-table:column-widths",
      JSON.stringify({ name: 150, createdAt: 200 }),
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "test-table:column-widths",
      JSON.stringify({}),
    );
  });

  it("persists column widths across hook instances", () => {
    // Set up localStorage with existing column widths
    localStorageMock.setItem(
      "test-table:column-widths",
      JSON.stringify({ name: 120, status: 80 }),
    );

    const { result } = renderHook(() =>
      useTableState<SortKey>({
        tableId: "test-table",
      }),
    );

    // Column widths should be loaded from localStorage
    expect(result.current.columnWidths).toEqual({ name: 120, status: 80 });
  });
});
