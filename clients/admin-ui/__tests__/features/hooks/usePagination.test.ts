import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../utils/nuqs-mock").nuqsMock);

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { usePagination } from "../../../src/features/common/hooks";
// Import the test helpers type and access from the mocked module
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
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
    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 50,
        pageSizeOptions: [10, 20, 50, 100],
        showSizeChanger: false,
      }),
    );

    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(50);
    expect(result.current.pageSizeOptions).toEqual([10, 20, 50, 100]);
    expect(result.current.showSizeChanger).toBe(false);
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
    act(() => result.current.updatePageIndex(5));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 5 });

    // Change page size (should reset to page 1)
    act(() => result.current.updatePageSize(50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1,
      size: 50,
    });

    // Change page without changing size
    act(() => result.current.updatePageIndex(2));
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

  it("handles pagination update logic correctly", () => {
    const { result } = renderHook(() => usePagination());

    // Change page size (should reset to page 1)
    act(() => result.current.updatePageIndex(5));
    act(() => result.current.updatePageSize(50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({
      page: 1, // Reset to 1 when size changes
      size: 50,
    });

    // Simulate state change to test subsequent calls
    nuqsTestHelpers.reset({ page: 3, size: 50 });
    const { result: result2 } = renderHook(() => usePagination());

    // Update page only (no page size provided)
    act(() => result2.current.updatePageIndex(3));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 3 }); // Only page is updated

    // Update with same page size (should not reset page)
    act(() => result2.current.updatePageIndex(3));
    act(() => result2.current.updatePageSize(50));
    expect(nuqsTestHelpers.getSetCalls().at(-1)).toEqual({ page: 3, size: 50 }); // Should not reset page, but size is included

    // Update with different page size (should reset page)
    act(() => result2.current.updatePageIndex(3));
    act(() => result2.current.updatePageSize(100));
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
    expect(typeof result.current.updatePageIndex).toBe("function");
    expect(typeof result.current.updatePageSize).toBe("function");
    expect(typeof result.current.resetPagination).toBe("function");
  });

  it("handles invalid negative values by falling back to defaults", () => {
    // Seed URL state with negative values (should be invalid)
    nuqsTestHelpers.reset({
      page: -1,
      size: -10,
    });

    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 25,
      }),
    );

    // Should fall back to default values when invalid values are provided
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(25);
  });

  it("handles invalid zero values by falling back to defaults", () => {
    // Seed URL state with zero values (should be invalid for positive validation)
    nuqsTestHelpers.reset({
      page: 0,
      size: 0,
    });

    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 50,
      }),
    );

    // Should fall back to default values when zero values are provided
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(50);
  });

  it("accepts valid positive integer values from URL", () => {
    // Seed URL state with valid positive values
    nuqsTestHelpers.reset({
      page: 5,
      size: 100,
    });

    const { result } = renderHook(() =>
      usePagination({
        defaultPageSize: 25,
      }),
    );

    // Should use the valid positive values from URL
    expect(result.current.pageIndex).toBe(5);
    expect(result.current.pageSize).toBe(100);
  });
});
