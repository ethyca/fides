import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../../utils/nuqs-mock").nuqsMock);

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
  });

  it("manages table state with custom configuration", () => {
    const onStateChange = jest.fn();
    const { result } = renderHook(() =>
      useTableState<SortKey>({
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
  });

  describe("with disableUrlState: true", () => {
    it("initializes with default values without using URL state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: { defaultPageSize: 30 },
          sorting: {
            defaultSortKey: "name",
            defaultSortOrder: "ascend",
          },
        }),
      );

      expect(result.current.pageIndex).toBe(1);
      expect(result.current.pageSize).toBe(30);
      expect(result.current.sortKey).toBe("name");
      expect(result.current.sortOrder).toBe("ascend");
      expect(result.current.columnFilters).toEqual({});
      expect(result.current.searchQuery).toBeUndefined();
    });

    it("does not read from URL when disableUrlState is true", () => {
      // Seed URL state with values
      nuqsTestHelpers.reset({
        page: 5,
        size: 50,
        sortKey: "title",
        sortOrder: "descend",
        filters: { status: ["active"] },
        search: "test query",
      });

      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: { defaultPageSize: 30 },
          sorting: {
            defaultSortKey: "name",
            defaultSortOrder: "ascend",
          },
        }),
      );

      // Should use default values instead of URL values
      expect(result.current.pageIndex).toBe(1);
      expect(result.current.pageSize).toBe(30);
      expect(result.current.sortKey).toBe("name");
      expect(result.current.sortOrder).toBe("ascend");
      expect(result.current.columnFilters).toEqual({});
      expect(result.current.searchQuery).toBeUndefined();
    });

    it("does not call setQueryState when updating table state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
        }),
      );

      const initialCallCount = nuqsTestHelpers.getSetCalls().length;

      // Update various table features
      act(() => result.current.updatePageIndex(3));
      expect(result.current.pageIndex).toBe(3);

      act(() => result.current.updateSorting("title", "descend"));
      // Note: updating sorting resets page to 1
      expect(result.current.pageIndex).toBe(1);

      act(() => result.current.updatePageIndex(2));
      expect(result.current.pageIndex).toBe(2);

      act(() => result.current.updateFilters({ status: ["active"] }));
      // Note: updating filters resets page to 1
      expect(result.current.pageIndex).toBe(1);

      act(() => result.current.updatePageIndex(3));
      expect(result.current.pageIndex).toBe(3);

      act(() => result.current.updateSearch("test"));
      // Note: updating search resets page to 1
      expect(result.current.pageIndex).toBe(1);

      // Should not have called setQueryState
      expect(nuqsTestHelpers.getSetCalls().length).toBe(initialCallCount);

      // Verify final state
      expect(result.current.sortKey).toBe("title");
      expect(result.current.sortOrder).toBe("descend");
      expect(result.current.columnFilters).toEqual({ status: ["active"] });
      expect(result.current.searchQuery).toBe("test");
    });

    it("updates all table features correctly without URL state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: { defaultPageSize: 25 },
        }),
      );

      // Update pagination
      act(() => result.current.updatePageIndex(2));
      expect(result.current.pageIndex).toBe(2);

      act(() => result.current.updatePageSize(50));
      expect(result.current.pageSize).toBe(50);
      expect(result.current.pageIndex).toBe(1); // Should reset to 1 when page size changes

      // Update sorting
      act(() => result.current.updateSorting("createdAt", "descend"));
      expect(result.current.sortKey).toBe("createdAt");
      expect(result.current.sortOrder).toBe("descend");
      expect(result.current.pageIndex).toBe(1);

      // Update page again
      act(() => result.current.updatePageIndex(3));
      expect(result.current.pageIndex).toBe(3);

      // Update filters
      act(() =>
        result.current.updateFilters({ role: ["admin"], status: ["active"] }),
      );
      expect(result.current.columnFilters).toEqual({
        role: ["admin"],
        status: ["active"],
      });
      expect(result.current.pageIndex).toBe(1);

      // Update page again
      act(() => result.current.updatePageIndex(2));
      expect(result.current.pageIndex).toBe(2);

      // Update search
      act(() => result.current.updateSearch("search query"));
      expect(result.current.searchQuery).toBe("search query");
      expect(result.current.pageIndex).toBe(1);
    });

    it("resets all table state correctly without URL state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: { defaultPageSize: 25 },
          sorting: {
            defaultSortKey: "name",
            defaultSortOrder: "ascend",
          },
        }),
      );

      // Update sorting
      act(() => result.current.updateSorting("title", "descend"));
      expect(result.current.sortKey).toBe("title");
      expect(result.current.sortOrder).toBe("descend");
      expect(result.current.pageIndex).toBe(1);

      // Set page to 5
      act(() => result.current.updatePageIndex(5));
      expect(result.current.pageIndex).toBe(5);

      // Update filters
      act(() => result.current.updateFilters({ status: ["active"] }));
      expect(result.current.columnFilters).toEqual({ status: ["active"] });
      expect(result.current.pageIndex).toBe(1);

      // Set page again
      act(() => result.current.updatePageIndex(3));
      expect(result.current.pageIndex).toBe(3);

      // Update search
      act(() => result.current.updateSearch("test"));
      expect(result.current.searchQuery).toBe("test");
      expect(result.current.pageIndex).toBe(1);

      // Set page one more time for final check
      act(() => result.current.updatePageIndex(2));

      // Verify all state before reset
      expect(result.current.pageIndex).toBe(2);
      expect(result.current.pageSize).toBe(25);
      expect(result.current.sortKey).toBe("title");
      expect(result.current.sortOrder).toBe("descend");
      expect(result.current.columnFilters).toEqual({ status: ["active"] });
      expect(result.current.searchQuery).toBe("test");

      // Reset state
      act(() => result.current.resetState());

      // Should reset to defaults
      expect(result.current.pageIndex).toBe(1);
      expect(result.current.pageSize).toBe(25);
      expect(result.current.sortKey).toBe("name");
      expect(result.current.sortOrder).toBe("ascend");
      expect(result.current.columnFilters).toEqual({});
      expect(result.current.searchQuery).toBeUndefined();
    });

    it("calls onStateChange callback with local state", () => {
      const onStateChange = jest.fn();

      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: { defaultPageSize: 30 },
          sorting: {
            defaultSortKey: "name",
            defaultSortOrder: "ascend",
          },
          onStateChange,
        }),
      );

      // Should be called on initial render
      expect(onStateChange).toHaveBeenCalledWith(
        expect.objectContaining({
          pageIndex: 1,
          pageSize: 30,
          sortKey: "name",
          sortOrder: "ascend",
        }),
      );

      // Update state
      act(() => result.current.updateSorting("title", "descend"));

      // Should be called with updated state
      expect(onStateChange).toHaveBeenCalledWith(
        expect.objectContaining({
          sortKey: "title",
          sortOrder: "descend",
        }),
      );
    });

    it("handles filter updates correctly without URL state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
        }),
      );

      // Add filters
      act(() =>
        result.current.updateFilters({
          status: ["active"],
          role: ["admin"],
        }),
      );
      expect(result.current.columnFilters).toEqual({
        status: ["active"],
        role: ["admin"],
      });

      // Update filters
      act(() =>
        result.current.updateFilters({
          status: ["inactive"],
          role: ["admin"],
          priority: ["high"],
        }),
      );
      expect(result.current.columnFilters).toEqual({
        status: ["inactive"],
        role: ["admin"],
        priority: ["high"],
      });

      // Clear filters
      act(() => result.current.updateFilters({}));
      expect(result.current.columnFilters).toEqual({});
    });

    it("maintains pagination config correctly without URL state", () => {
      const { result } = renderHook(() =>
        useTableState<SortKey>({
          disableUrlState: true,
          pagination: {
            defaultPageSize: 50,
            pageSizeOptions: [25, 50, 100],
            showSizeChanger: false,
          },
        }),
      );

      expect(result.current.paginationConfig).toEqual({
        pageSizeOptions: [25, 50, 100],
        showSizeChanger: false,
      });
    });
  });
});
