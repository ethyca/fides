import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { renderHook } from "@testing-library/react";

// Mock nuqs using shared mock implementation
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../utils/nuqs-mock").nuqsMock);

// Import after mocks so the mocked nuqs is used by the hook
// eslint-disable-next-line import/first
import { useAntPagination } from "../../../src/features/common/hooks";
// Import the test helpers type and access from the mocked module
// eslint-disable-next-line import/first
import type { NuqsTestHelpers } from "../../utils/nuqs-mock";

const { nuqsTestHelpers } = jest.requireMock("nuqs") as {
  nuqsTestHelpers: NuqsTestHelpers;
};

describe("useAntPagination", () => {
  beforeEach(() => {
    nuqsTestHelpers.reset();
  });

  it("provides all pagination functionality from usePagination", () => {
    const { result } = renderHook(() => useAntPagination());

    // Should include all core pagination functionality
    expect(result.current.pageIndex).toBe(1);
    expect(result.current.pageSize).toBe(25);
    expect(result.current.pageSizeOptions).toEqual([25, 50, 100]);
    expect(result.current.showSizeChanger).toBe(true);
    expect(typeof result.current.updatePageIndex).toBe("function");
    expect(typeof result.current.updatePageSize).toBe("function");
    expect(typeof result.current.resetPagination).toBe("function");
  });

  it("provides Ant Design pagination props", () => {
    const { result } = renderHook(() =>
      useAntPagination({
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
      onChange: expect.any(Function),
      onShowSizeChange: expect.any(Function),
    });
  });

  it("provides callable functions in paginationProps across re-renders", () => {
    const { result, rerender } = renderHook(() =>
      useAntPagination({
        defaultPageSize: 25,
      }),
    );

    // Re-render the hook
    rerender();

    // Functions should exist and be callable
    expect(typeof result.current.paginationProps.onChange).toBe("function");
    expect(typeof result.current.paginationProps.onShowSizeChange).toBe(
      "function",
    );
  });

  it("updates paginationProps when underlying state changes", () => {
    // Seed URL state with pagination values
    nuqsTestHelpers.reset({
      page: 3,
      size: 100,
    });

    const { result } = renderHook(() =>
      useAntPagination({
        defaultPageSize: 25,
        pageSizeOptions: [25, 50, 100, 200],
      }),
    );

    const { paginationProps } = result.current;

    expect(paginationProps.current).toBe(3);
    expect(paginationProps.pageSize).toBe(100);
    expect(paginationProps.pageSizeOptions).toEqual(["25", "50", "100", "200"]);
  });

  it("converts pageSizeOptions to strings for Ant Design", () => {
    const { result } = renderHook(() =>
      useAntPagination({
        pageSizeOptions: [10, 25, 50, 100],
      }),
    );

    expect(result.current.paginationProps.pageSizeOptions).toEqual([
      "10",
      "25",
      "50",
      "100",
    ]);
  });

  it("configures showSizeChanger correctly", () => {
    const { result: resultWithSizeChanger } = renderHook(() =>
      useAntPagination({
        showSizeChanger: true,
      }),
    );

    const { result: resultWithoutSizeChanger } = renderHook(() =>
      useAntPagination({
        showSizeChanger: false,
      }),
    );

    expect(resultWithSizeChanger.current.paginationProps.showSizeChanger).toBe(
      true,
    );
    expect(
      resultWithoutSizeChanger.current.paginationProps.showSizeChanger,
    ).toBe(false);
  });
});
