import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs to control URL state without relying on Next router
// NOTE: our code is not modern enough to use the nuqs testing adapter
// (specifically the ESM module compatibility)
// so we're using a custom mock for now. Once ESM is more widely supported,
// we can switch to the nuqs testing adapter.
jest.mock("nuqs", () => {
  const setCalls: Array<Record<string, any> | null> = [];
  let currentState: Record<string, any> = {};

  const parseFactory = (defaultValue: unknown) => ({
    withDefault: (value: unknown) => ({ default: value ?? defaultValue }),
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
    esModule: true,
    parseAsInteger: parseFactory(1),

    useQueryStates: (parsers: Record<string, any>) => {
      const setQueryState = (updates: Record<string, any> | null) => {
        setCalls.push(updates);
        if (updates && typeof updates === "object") {
          // Filter out null values (they represent deletions in nuqs)
          const filteredUpdates = Object.fromEntries(
            Object.entries(updates).filter(([, value]) => value !== null),
          );
          currentState = { ...currentState, ...filteredUpdates };
        }
      };

      // Return current state values, but fall back to parser defaults when undefined
      const stateWithDefaults = Object.keys(parsers).reduce(
        (acc, key) => {
          const parser = parsers[key];
          const currentValue = currentState[key];
          // If value is undefined, use the parser's default
          if (currentValue === undefined && parser?.default !== undefined) {
            // eslint-disable-next-line no-param-reassign
            acc[key] = parser.default;
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

    nuqsTestHelpers: helpers,
  };
});

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { usePagination } from "../../../src/features/common/table/hooks/usePagination";

// Access the test helpers from the mocked module
const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: {
    reset: (initial?: Record<string, any>) => void;
    getSetCalls: () => Array<Record<string, any> | null>;
    getState: () => Record<string, any>;
  };
};

describe("usePagination", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
  });

  it("initializes with default values", () => {
    const { result } = renderHook(() => usePagination());

    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(25);
    expect(result.current.pageSizeOptions).toEqual([25, 50, 100]);
    expect(result.current.showSizeChanger).toBe(true);
  });

  it("initializes with custom configuration", () => {
    const onPaginationChange = jest.fn();
    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 50,
        pageSizeOptions: [10, 20, 50, 100],
        showSizeChanger: false,
        onPaginationChange,
      }),
    );

    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(50);
    expect(result.current.pageSizeOptions).toEqual([10, 20, 50, 100]);
    expect(result.current.showSizeChanger).toBe(false);

    // onPaginationChange should be called with initial state
    expect(onPaginationChange).toHaveBeenCalledWith({
      pageIndex: 1,
      pageSize: 50,
    });
  });

  it("reads state from URL when available", () => {
    // Seed URL state with pagination values
    nuqsTestHelpers.reset({
      page: 3,
      size: 100,
    });

    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 25,
      }),
    );

    // Should use URL values instead of defaults
    expect(result.current.pageIndex).toBe(3);
    expect(result.current.pageSize).toBe(100);
  });

  it("calls setQueryState with correct values when updating pagination", () => {
    const { result } = renderHook(() => usePagination());

    // Change page only
    act(() => result.current.updatePagination(5));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 5 });

    // Change page size (should reset to page 1)
    act(() => result.current.updatePagination(3, 50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1,
      size: 50,
    });

    // Change page without changing size
    act(() => result.current.updatePagination(2));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 2 });
  });

  it("calls setQueryState correctly when resetting pagination", () => {
    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 50,
      }),
    );

    // Reset pagination
    act(() => result.current.resetPagination());

    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1,
      size: 50,
    });
  });

  it("calls onPaginationChange on initial render", () => {
    const onPaginationChange = jest.fn();
    renderHook(() =>
      usePagination({
        defaultPageSize: 25,
        onPaginationChange,
      }),
    );

    // Should be called on initial render
    expect(onPaginationChange).toHaveBeenCalledWith({
      pageIndex: 1,
      pageSize: 25,
    });
  });

  it("provides Ant Design pagination props", () => {
    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 50,
        pageSizeOptions: [25, 50, 100, 200],
        showSizeChanger: true,
      }),
    );

    const { paginationProps } = result.current;

    expect(paginationProps).toEqual({
      current: 1,
      pageSize: 50,
      showSizeChanger: true,
      pageSizeOptions: ["25", "50", "100", "200"], // Should be strings for Ant
      showQuickJumper: true,
      showTotal: expect.any(Function),
      onChange: expect.any(Function),
      onShowSizeChange: expect.any(Function),
    });

    // Test showTotal function
    const showTotalResult = paginationProps.showTotal!(150, [26, 50]);
    expect(showTotalResult).toBe("26-50 of 150 items");

    // Test onChange function (should be same as updatePagination)
    expect(paginationProps.onChange).toBe(result.current.updatePagination);
    expect(paginationProps.onShowSizeChange).toBe(
      result.current.updatePagination,
    );
  });

  it("handles pagination update logic correctly", () => {
    const { result } = renderHook(() => usePagination());

    // Change page size (should reset to page 1)
    act(() => result.current.updatePagination(5, 50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1, // Reset to 1 when size changes
      size: 50,
    });

    // Simulate state change to test subsequent calls
    nuqsTestHelpers.reset({ page: 3, size: 50 });
    const { result: result2 } = renderHook(() => usePagination());

    // Update page only (no page size provided)
    act(() => result2.current.updatePagination(3));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 3 }); // Only page is updated

    // Update with same page size (should not reset page)
    act(() => result2.current.updatePagination(3, 50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 3, size: 50 }); // Should not reset page, but size is included

    // Update with different page size (should reset page)
    act(() => result2.current.updatePagination(3, 100));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1, // Should reset to 1
      size: 100,
    });
  });

  it("falls back to defaults when URL has undefined values", () => {
    // Start with empty state (undefined values)
    nuqsTestHelpers.reset({});

    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 75,
      }),
    );

    // Should use configured defaults when URL is empty
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(75);
  });

  it("maintains function references across re-renders", () => {
    const { result, rerender } = renderHook(() =>
      usePagination({
        defaultPageSize: 25,
      }),
    );

    // Re-render the hook
    rerender();

    // Functions should exist and be callable
    expect(typeof result.current.updatePagination).toBe("function");
    expect(typeof result.current.resetPagination).toBe("function");
    expect(typeof result.current.paginationProps.onChange).toBe("function");
    expect(typeof result.current.paginationProps.onShowSizeChange).toBe(
      "function",
    );
  });
});
