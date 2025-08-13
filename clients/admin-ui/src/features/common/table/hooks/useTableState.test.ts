import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs to control URL state without relying on Next router
jest.mock("nuqs", () => {
  const setCalls: Array<Record<string, any> | null> = [];
  let currentState: Record<string, any> = {};

  const parseFactory = (defaultValue: unknown) => ({
    withDefault: (value: unknown) => ({ __default: value ?? defaultValue }),
  });

  const helpers = {
    reset: (initial: Record<string, any> = {}) => {
      currentState = { ...initial };
      setCalls.length = 0;
    },
    getSetCalls: () => setCalls,
    getState: () => currentState,
  };

  return {
    __esModule: true,
    // Minimal parser mocks; only shape is required
    // Note: parseAsString defaults to empty string, which is falsy and affects || logic
    parseAsInteger: parseFactory(1),
    parseAsString: parseFactory(""),
    parseAsJson: () => ({
      withDefault: (value: unknown) => ({ __default: value }),
    }),

    useQueryStates: (parsers: Record<string, any>) => {
      const setQueryState = (updates: Record<string, any> | null) => {
        setCalls.push(updates);
        if (updates && typeof updates === "object") {
          currentState = { ...currentState, ...updates };
        }
      };

      // Return current state values, but fall back to parser defaults when undefined
      const stateWithDefaults = Object.keys(parsers).reduce(
        (acc, key) => {
          const parser = parsers[key];
          const currentValue = currentState[key];
          // If value is undefined, use the parser's default
          // eslint-disable-next-line no-underscore-dangle
          if (currentValue === undefined && parser?.__default !== undefined) {
            // eslint-disable-next-line no-param-reassign, no-underscore-dangle
            acc[key] = parser.__default;
          } else {
            // eslint-disable-next-line no-param-reassign
            acc[key] = currentValue;
          }
          return acc;
        },
        {} as Record<string, any>,
      );

      return [stateWithDefaults, setQueryState] as const;
    },

    // Test-only helpers (also returned to module consumers if needed)
    nuqsTestHelpers: helpers,
  };
});

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { useTableState } from "./useTableState";

// Access the test helpers from the mocked module
const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: {
    reset: (initial?: Record<string, any>) => void;
    getSetCalls: () => Array<Record<string, any> | null>;
    getState: () => Record<string, any>;
  };
};

type SortField = "name" | "createdAt" | "title";

describe("useTableState", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
  });

  it("manages state with custom configuration", () => {
    const onStateChange = jest.fn();
    const { result } = renderHook(() =>
      useTableState<SortField>({
        pagination: {
          defaultPageSize: 30,
          pageSizeOptions: [10, 20, 30],
          showSizeChanger: false,
        },
        sorting: {
          defaultSortField: "name",
          defaultSortOrder: "ascend",
        },
        onStateChange,
      }),
    );

    // Initial state reflects internal defaults
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(30);
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");
    expect(result.current.columnFilters).toEqual({});
    expect(result.current.searchQuery).toBeUndefined();
    expect(result.current.paginationConfig).toEqual({
      pageSizeOptions: [10, 20, 30],
      showSizeChanger: false,
    });

    // Pagination: changing page size resets to first page
    act(() => result.current.updatePagination(2, 40));
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(40);

    // Sorting: updates and resets to first page
    act(() => result.current.updateSorting("createdAt", "descend"));
    expect(result.current.sortField).toBe("createdAt");
    expect(result.current.sortOrder).toBe("descend");
    expect(result.current.pageIndex).toBe(1);

    // Filtering: updates and resets to first page
    act(() => result.current.updateFilters({ status: ["active"] }));
    expect(result.current.columnFilters).toEqual({ status: ["active"] });
    expect(result.current.pageIndex).toBe(1);

    // Search: updates and resets to first page
    act(() => result.current.updateSearch("query"));
    expect(result.current.searchQuery).toBe("query");
    expect(result.current.pageIndex).toBe(1);

    // Reset restores defaults
    act(() => result.current.resetState());
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(30);
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");
    expect(result.current.columnFilters).toEqual({});
    expect(result.current.searchQuery).toBeUndefined();

    // onStateChange called with updated state
    expect(onStateChange).toHaveBeenCalled();
  });

  it("uses URL state and updates URL when urlSync is enabled", () => {
    // Seed URL state with meaningful values (not empty strings that would be treated as falsy)
    nuqsTestHelpers.reset({
      page: 3,
      size: 10,
      sortField: "name",
      sortOrder: "ascend",
      filters: { role: ["admin"] }, // Remove null values as they get filtered out
      search: "abc",
    });

    const { result } = renderHook(() =>
      useTableState<SortField>({
        // Default urlSync is all true
        pagination: { defaultPageSize: 25 },
        sorting: {
          defaultSortField: "createdAt",
          defaultSortOrder: "descend",
        },
      }),
    );

    // Current state reflects URL values
    expect(result.current.pageIndex).toBe(3);
    expect(result.current.pageSize).toBe(10);
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");
    expect(result.current.columnFilters).toEqual({
      role: ["admin"],
    });
    expect(result.current.searchQuery).toBe("abc");

    // Pagination: page change
    act(() => result.current.updatePagination(5));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 5 });

    // Pagination: page size change resets page to 1
    act(() => result.current.updatePagination(4, 50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1,
      size: 50,
    });

    // Sorting: set values and reset page
    act(() => result.current.updateSorting("title", "descend"));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      sortField: "title",
      sortOrder: "descend",
      page: 1,
    });

    // Sorting: clear values
    act(() => result.current.updateSorting(undefined, undefined));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      sortField: null,
      sortOrder: null,
      page: 1,
    });

    // Filters: remove null/undefined and reset page
    act(() =>
      result.current.updateFilters({
        role: ["user"],
        empty: null,
      }),
    );
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      filters: { role: ["user"] },
      page: 1,
    });

    // Filters: when empty, use null and reset page
    act(() => result.current.updateFilters({}));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      filters: null,
      page: 1,
    });

    // Search: set and clear
    act(() => result.current.updateSearch("find me"));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      search: "find me",
      page: 1,
    });
    act(() => result.current.updateSearch(undefined));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      search: null,
      page: 1,
    });

    // Reset: resets all URL-managed fields to defaults
    act(() => result.current.resetState());
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1,
      size: 25,
      sortField: null,
      sortOrder: null,
      filters: null,
      search: null,
    });
  });

  it("handles empty/default URL values correctly", () => {
    // Seed URL state with empty string values (which are the defaults from parsers)
    nuqsTestHelpers.reset({
      page: 1,
      size: 25,
      sortField: "", // Empty string from parser default
      sortOrder: "", // Empty string from parser default
      filters: {},
      search: "", // Empty string from parser default
    });

    const { result } = renderHook(() =>
      useTableState<SortField>({
        pagination: { defaultPageSize: 25 },
        sorting: {
          defaultSortField: "createdAt",
          defaultSortOrder: "descend",
        },
      }),
    );

    // Should fall back to configured defaults when URL has empty strings
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(25);
    expect(result.current.sortField).toBe("createdAt"); // Falls back to default because "" is falsy
    expect(result.current.sortOrder).toBe("descend"); // Falls back to default because "" is falsy
    expect(result.current.columnFilters).toEqual({});
    expect(result.current.searchQuery).toBe(""); // Empty string from URL is preserved
  });
});
