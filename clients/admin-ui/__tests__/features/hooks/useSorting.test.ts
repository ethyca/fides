import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../utils/nuqs-mock").nuqsMock);

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { useSorting } from "../../../src/features/common/hooks";
// Import the test helpers type and access from the mocked module
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
};

type SortField = "name" | "createdAt" | "title" | "status";

describe("useSorting", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
  });

  it("initializes with default values", () => {
    const { result } = renderHook(() => useSorting());

    // Initial state should have undefined values when no defaults are provided
    expect(result.current.sortField).toBeUndefined();
    expect(result.current.sortOrder).toBeUndefined();

    // Functions should be available
    expect(typeof result.current.updateSorting).toBe("function");
    expect(typeof result.current.resetSorting).toBe("function");

    // Ant Design props should be provided
    expect(result.current.sortingProps).toEqual({
      sortDirections: ["ascend", "descend"],
      defaultSortOrder: undefined,
      sortedInfo: undefined,
    });
  });

  it("initializes with custom configuration", () => {
    const onSortingChange = jest.fn();
    const { result } = renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "name",
        defaultSortOrder: "ascend",
        onSortingChange,
      }),
    );

    // Initial state should reflect configuration defaults
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");

    // Ant Design props should reflect current state
    expect(result.current.sortingProps).toEqual({
      sortDirections: ["ascend", "descend"],
      defaultSortOrder: "ascend",
      sortedInfo: {
        field: "name",
        order: "ascend",
      },
    });

    // Callback should be called with initial state
    expect(onSortingChange).toHaveBeenCalledWith({
      sortField: "name",
      sortOrder: "ascend",
    });
  });

  it("reads state from URL when available", () => {
    // Seed URL state with sorting values
    nuqsTestHelpers.reset({
      sortField: "createdAt",
      sortOrder: "descend",
    });

    const { result } = renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "name", // Should be overridden by URL
        defaultSortOrder: "ascend", // Should be overridden by URL
      }),
    );

    // Current state should reflect URL values, not defaults
    expect(result.current.sortField).toBe("createdAt");
    expect(result.current.sortOrder).toBe("descend");

    // Ant Design props should reflect URL state
    expect(result.current.sortingProps.defaultSortOrder).toBe("descend");
    expect(result.current.sortingProps.sortedInfo).toEqual({
      field: "createdAt",
      order: "descend",
    });
  });

  it("calls setQueryState with correct values when updating sorting", () => {
    const { result } = renderHook(() => useSorting<SortField>());

    act(() => {
      result.current.updateSorting("title", "ascend");
    });

    // Should have made one call to setQueryState
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      sortField: "title",
      sortOrder: "ascend",
    });
  });

  it("calls setQueryState correctly when updating only sort field", () => {
    const { result } = renderHook(() => useSorting<SortField>());

    act(() => {
      result.current.updateSorting("status");
    });

    // Should set field but clear order
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      sortField: "status",
      sortOrder: null,
    });
  });

  it("calls setQueryState correctly when updating only sort order", () => {
    const { result } = renderHook(() => useSorting<SortField>());

    act(() => {
      result.current.updateSorting(undefined, "descend");
    });

    // Should clear field but set order
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      sortField: null,
      sortOrder: "descend",
    });
  });

  it("calls setQueryState correctly when resetting sorting", () => {
    // Start with some sorting state
    nuqsTestHelpers.reset({
      sortField: "name",
      sortOrder: "ascend",
    });

    const { result } = renderHook(() => useSorting<SortField>());

    act(() => {
      result.current.resetSorting();
    });

    // Should have made one call to reset both values
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      sortField: null,
      sortOrder: null,
    });
  });

  it("calls onSortingChange on initial render", () => {
    const onSortingChange = jest.fn();

    renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "createdAt",
        defaultSortOrder: "descend",
        onSortingChange,
      }),
    );

    expect(onSortingChange).toHaveBeenCalledTimes(1);
    expect(onSortingChange).toHaveBeenCalledWith({
      sortField: "createdAt",
      sortOrder: "descend",
    });
  });

  it("provides correct Ant Design sorting props", () => {
    const { result } = renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "title",
        defaultSortOrder: "descend",
      }),
    );

    const { sortingProps } = result.current;

    expect(sortingProps.sortDirections).toEqual(["ascend", "descend"]);
    expect(sortingProps.defaultSortOrder).toBe("descend");
    expect(sortingProps.sortedInfo).toEqual({
      field: "title",
      order: "descend",
    });
  });

  it("provides undefined sortedInfo when no sorting is active", () => {
    const { result } = renderHook(() => useSorting<SortField>());

    expect(result.current.sortingProps.sortedInfo).toBeUndefined();
  });

  it("handles clearing sorting completely", () => {
    // Start with sorting active
    nuqsTestHelpers.reset({
      sortField: "name",
      sortOrder: "ascend",
    });

    const { result } = renderHook(() => useSorting<SortField>());

    // Verify initial state
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("ascend");

    // Clear sorting
    act(() => {
      result.current.updateSorting();
    });

    // Should have called setQueryState to clear both
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      sortField: null,
      sortOrder: null,
    });
  });

  it("falls back to defaults when URL has undefined values", () => {
    // Seed URL state with undefined values
    nuqsTestHelpers.reset({
      sortField: undefined,
      sortOrder: undefined,
    });

    const { result } = renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "status",
        defaultSortOrder: "ascend",
      }),
    );

    // Should fall back to configured defaults
    expect(result.current.sortField).toBe("status");
    expect(result.current.sortOrder).toBe("ascend");
  });

  it("falls back to defaults when URL has empty string and null values", () => {
    // Seed URL state with values that should trigger fallbacks
    nuqsTestHelpers.reset({
      sortField: "", // Empty string should trigger fallback with || operator
      sortOrder: null, // null should trigger fallback with ?? operator
    });

    const { result } = renderHook(() =>
      useSorting<SortField>({
        defaultSortField: "name",
        defaultSortOrder: "descend",
      }),
    );

    // Should fall back to configured defaults
    expect(result.current.sortField).toBe("name");
    expect(result.current.sortOrder).toBe("descend");
  });

  it("executes update and reset functions without errors", () => {
    const { result } = renderHook(() => useSorting<SortField>());

    // Test that functions execute without errors
    expect(() => {
      act(() => result.current.updateSorting("createdAt", "descend"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateSorting("status"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.resetSorting());
    }).not.toThrow();

    // Verify the calls were made
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(3);
    expect(setCalls[0]).toEqual({
      sortField: "createdAt",
      sortOrder: "descend",
    });
    expect(setCalls[1]).toEqual({ sortField: "status", sortOrder: null });
    expect(setCalls[2]).toEqual({ sortField: null, sortOrder: null });
  });

  it("handles URL state changes correctly", () => {
    // Test multiple URL state scenarios
    const testCases = [
      {
        urlState: { sortField: "name", sortOrder: "ascend" },
        expected: { sortField: "name", sortOrder: "ascend" },
      },
      {
        urlState: { sortField: "title", sortOrder: "descend" },
        expected: { sortField: "title", sortOrder: "descend" },
      },
      {
        urlState: { sortField: "", sortOrder: null },
        expected: { sortField: undefined, sortOrder: undefined }, // Should use defaults (undefined)
      },
    ];

    testCases.forEach(({ urlState, expected }) => {
      nuqsTestHelpers.reset(urlState);
      const { result } = renderHook(() => useSorting<SortField>());

      expect(result.current.sortField).toBe(expected.sortField);
      expect(result.current.sortOrder).toBe(expected.sortOrder);
    });
  });
});
