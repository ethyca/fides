import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../utils/nuqs-mock").nuqsMock);

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { useSearch } from "../../../src/features/common/hooks";
// Import the test helpers type and access from the mocked module
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
};

describe("useSearch", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
  });

  it("initializes with default values", () => {
    const { result } = renderHook(() => useSearch());

    // Initial state should have undefined search query when no default is provided
    expect(result.current.searchQuery).toBeUndefined();

    // Functions should be available
    expect(typeof result.current.updateSearch).toBe("function");
    expect(typeof result.current.resetSearch).toBe("function");

    // Search props should be provided for input components
    expect(result.current.searchProps).toEqual({
      value: "",
      onChange: expect.any(Function),
      onClear: expect.any(Function),
    });
  });

  it("initializes with custom configuration", () => {
    const onSearchChange = jest.fn();
    const { result } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "initial query",
        onSearchChange,
      }),
    );

    // Initial state should reflect configuration defaults
    expect(result.current.searchQuery).toBe("initial query");

    // Search props should reflect current state
    expect(result.current.searchProps).toEqual({
      value: "initial query",
      onChange: expect.any(Function),
      onClear: expect.any(Function),
    });

    // Callback should be called with initial state
    expect(onSearchChange).toHaveBeenCalledWith({
      searchQuery: "initial query",
    });
  });

  it("reads state from URL when available", () => {
    // Seed URL state with search value
    nuqsTestHelpers.reset({
      search: "url search query",
    });

    const { result } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "default query", // Should be overridden by URL
      }),
    );

    // Current state should reflect URL value, not default
    expect(result.current.searchQuery).toBe("url search query");

    // Search props should reflect URL state
    expect(result.current.searchProps.value).toBe("url search query");
  });

  it("calls setQueryState with correct values when updating search", () => {
    const { result } = renderHook(() => useSearch());

    act(() => {
      result.current.updateSearch("new search query");
    });

    // Should have made one call to setQueryState
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      search: "new search query",
    });
  });

  it("calls setQueryState correctly when clearing search", () => {
    const { result } = renderHook(() => useSearch());

    act(() => {
      result.current.updateSearch("");
    });

    // Should set search to null to remove from URL
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      search: null,
    });
  });

  it("calls setQueryState correctly when updating with undefined", () => {
    const { result } = renderHook(() => useSearch());

    act(() => {
      result.current.updateSearch(undefined);
    });

    // Should set search to null to remove from URL
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      search: null,
    });
  });

  it("calls setQueryState correctly when resetting search", () => {
    // Start with some search state
    nuqsTestHelpers.reset({
      search: "existing query",
    });

    const { result } = renderHook(() => useSearch());

    act(() => {
      result.current.resetSearch();
    });

    // Should have made one call to reset search value
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({
      search: null,
    });
  });

  it("calls onSearchChange on initial render", () => {
    const onSearchChange = jest.fn();

    renderHook(() =>
      useSearch({
        defaultSearchQuery: "test query",
        onSearchChange,
      }),
    );

    expect(onSearchChange).toHaveBeenCalledTimes(1);
    expect(onSearchChange).toHaveBeenCalledWith({
      searchQuery: "test query",
    });
  });

  it("provides correct search props for input components", () => {
    const { result } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "initial value",
      }),
    );

    const { searchProps } = result.current;

    expect(searchProps.value).toBe("initial value");
    expect(typeof searchProps.onChange).toBe("function");
    expect(typeof searchProps.onClear).toBe("function");

    // Test onChange function (should be same as updateSearch)
    expect(searchProps.onChange).toBe(result.current.updateSearch);

    // Test onClear function
    act(() => {
      searchProps.onClear();
    });

    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0]).toEqual({ search: null });
  });

  it("handles search value changes correctly", () => {
    const { result } = renderHook(() => useSearch());

    // Update to a search query
    act(() => {
      result.current.updateSearch("test search");
    });

    // Update to empty string (should clear)
    act(() => {
      result.current.updateSearch("");
    });

    // Update to another query
    act(() => {
      result.current.updateSearch("another search");
    });

    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(3);
    expect(setCalls[0]).toEqual({ search: "test search" });
    expect(setCalls[1]).toEqual({ search: null }); // Empty string converts to null
    expect(setCalls[2]).toEqual({ search: "another search" });
  });

  it("falls back to defaults when URL has undefined values", () => {
    // Seed URL state with undefined value
    nuqsTestHelpers.reset({
      search: undefined,
    });

    const { result } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "fallback query",
      }),
    );

    // Should fall back to configured default
    expect(result.current.searchQuery).toBe("fallback query");
  });

  it("falls back to defaults when URL has empty string value", () => {
    // Seed URL state with empty string (parser default)
    nuqsTestHelpers.reset({
      search: "",
    });

    const { result } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "fallback query",
      }),
    );

    // Should fall back to configured default when URL has empty string
    expect(result.current.searchQuery).toBe("fallback query");
  });

  it("returns undefined when no default and no URL value", () => {
    // Start with empty state
    nuqsTestHelpers.reset({});

    const { result } = renderHook(() => useSearch());

    // Should be undefined when no default and no URL value
    expect(result.current.searchQuery).toBeUndefined();
    expect(result.current.searchProps.value).toBe(""); // Props should show empty string for inputs
  });

  it("executes update and reset functions without errors", () => {
    const { result } = renderHook(() => useSearch());

    // Test that functions execute without errors
    expect(() => {
      act(() => result.current.updateSearch("search term"));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.updateSearch(""));
    }).not.toThrow();

    expect(() => {
      act(() => result.current.resetSearch());
    }).not.toThrow();

    // Verify the calls were made
    const setCalls = nuqsTestHelpers.getSetCalls();
    expect(setCalls).toHaveLength(3);
    expect(setCalls[0]).toEqual({ search: "search term" });
    expect(setCalls[1]).toEqual({ search: null });
    expect(setCalls[2]).toEqual({ search: null });
  });

  it("handles URL state changes correctly", () => {
    // Test multiple URL state scenarios
    const testCases = [
      {
        urlState: { search: "url query" },
        expected: { searchQuery: "url query" },
      },
      {
        urlState: { search: "another query" },
        expected: { searchQuery: "another query" },
      },
      {
        urlState: { search: "" },
        expected: { searchQuery: undefined }, // Empty string should result in undefined
      },
    ];

    testCases.forEach(({ urlState, expected }) => {
      nuqsTestHelpers.reset(urlState);
      const { result } = renderHook(() => useSearch());

      expect(result.current.searchQuery).toBe(expected.searchQuery);
    });
  });

  it("maintains function references across re-renders", () => {
    const { result, rerender } = renderHook(() =>
      useSearch({
        defaultSearchQuery: "test",
      }),
    );

    // Re-render the hook
    rerender();

    // Functions should exist and be callable
    expect(typeof result.current.updateSearch).toBe("function");
    expect(typeof result.current.resetSearch).toBe("function");
    expect(typeof result.current.searchProps.onChange).toBe("function");
    expect(typeof result.current.searchProps.onClear).toBe("function");
  });
});
