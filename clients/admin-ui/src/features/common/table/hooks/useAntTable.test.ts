import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";
import {
  AntFilterValue as FilterValue,
  AntTablePaginationConfig as TablePaginationConfig,
  AntTableProps as TableProps,
} from "fidesui";

import { SortOrder } from "./types";
import { useAntTable } from "./useAntTable";

type Row = { id?: string; key?: string; name: string };
type SortField = "name" | "createdAt";

interface MockTableState {
  pageIndex: number;
  pageSize: number;
  sortField?: SortField;
  sortOrder?: SortOrder;
  columnFilters: Record<string, FilterValue | null>;
  updatePagination: jest.MockedFunction<
    (pageIndex: number, pageSize?: number) => void
  >;
  updateSorting: jest.MockedFunction<
    (sortField?: SortField, sortOrder?: SortOrder) => void
  >;
  updateFilters: jest.MockedFunction<(filters: Record<string, any>) => void>;
  paginationConfig?: {
    pageSizeOptions: number[];
    showSizeChanger: boolean;
  };
}

const createTableState = (
  overrides: Partial<MockTableState> = {},
): MockTableState => {
  return {
    pageIndex: 1,
    pageSize: 25,
    sortField: undefined,
    sortOrder: undefined,
    columnFilters: {},
    updatePagination: jest.fn(),
    updateSorting: jest.fn(),
    updateFilters: jest.fn(),
    paginationConfig: {
      pageSizeOptions: [10, 25, 50],
      showSizeChanger: true,
    },
    ...overrides,
  };
};

const isPaginationConfig = (
  pagination: TableProps<any>["pagination"],
): pagination is TablePaginationConfig => {
  return pagination !== false && pagination != null;
};

describe("useAntTable", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns default table props and computes loading, pagination, and utilities", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        dataSource: [{ id: "1", name: "A" }],
        totalRows: 100,
        isLoading: true,
      }),
    );

    const { tableProps, isLoadingOrFetching, hasData } = result.current;

    expect(tableProps.dataSource).toEqual([{ id: "1", name: "A" }]);
    expect(tableProps.loading).toBe(true);
    expect(tableProps.pagination).toMatchObject({
      current: 1,
      pageSize: 25,
      total: 100,
      showSizeChanger: true,
      pageSizeOptions: ["10", "25", "50"],
      showQuickJumper: true,
    });
    if (isPaginationConfig(tableProps.pagination)) {
      const { showTotal } = tableProps.pagination;
      if (showTotal) {
        expect(showTotal(100, [1, 10])).toBe("1-10 of 100 items");
      }
    }
    expect(isLoadingOrFetching).toBe(true);
    expect(hasData).toBe(true);
  });

  it("honors config overrides for current page, page size, loading, and custom props", () => {
    const tableState = createTableState({
      paginationConfig: { pageSizeOptions: [5, 10], showSizeChanger: false },
    });
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        currentPage: 3,
        pageSize: 5,
        isFetching: true,
        customTableProps: { size: "large" },
      }),
    );

    const { tableProps, isLoadingOrFetching } = result.current;
    expect(tableProps.pagination).toMatchObject({
      current: 3,
      pageSize: 5,
      showSizeChanger: false,
      pageSizeOptions: ["5", "10"],
    });
    expect(isLoadingOrFetching).toBe(true);
    expect(tableProps.size).toBe("large");
  });

  it("provides a default rowKey that prefers id then key", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState),
    );
    const { tableProps } = result.current;

    const withId = { id: "abc", name: "A" } as Row;
    const withKey = { key: "k1", name: "B" } as Row;

    if (typeof tableProps.rowKey === "function") {
      expect(tableProps.rowKey(withId)).toBe("abc");
      expect(tableProps.rowKey(withKey)).toBe("k1");
    }
  });

  it("exposes selection props when enabled and supports updates/reset", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, { enableSelection: true }),
    );

    expect(result.current.selectionProps).toBeDefined();

    act(() => {
      result.current.selectionProps!.onChange(
        ["1", "2"],
        [
          { id: "1", name: "A" },
          { id: "2", name: "B" },
        ],
      );
    });

    expect(result.current.selectedRows).toHaveLength(2);
    expect(result.current.selectedKeys).toEqual(["1", "2"]);
    expect(result.current.hasSelectedRows).toBe(true);

    act(() => {
      result.current.resetSelections();
    });
    expect(result.current.selectedRows).toHaveLength(0);
    expect(result.current.selectedKeys).toHaveLength(0);
    expect(result.current.hasSelectedRows).toBe(false);
  });

  it("handles table change: pagination updates only when page or size differs", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState),
    );

    act(() => {
      // Simulate a pagination-only change
      result.current.tableProps.onChange?.(
        { current: 2, pageSize: 25 },
        {},
        { field: "name", order: "ascend" },
        {} as any,
      );
    });

    expect(tableState.updatePagination).toHaveBeenCalledWith(2, 25);
    expect(tableState.updateFilters).not.toHaveBeenCalled();
    expect(tableState.updateSorting).not.toHaveBeenCalled();
  });

  it("handles table change: sorting and filtering update when not a pagination change", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState),
    );

    act(() => {
      // Same page and size as current -> not a pagination change
      result.current.tableProps.onChange?.(
        { current: 1, pageSize: 25 },
        { status: ["active"] },
        { field: "name", order: "ascend" },
        {} as any,
      );
    });

    // When it's not a pagination change, call updateFilters and updateSorting
    expect(tableState.updateFilters).toHaveBeenCalledWith({
      status: ["active"],
    });
    expect(tableState.updateSorting).toHaveBeenCalledWith("name", "ascend");
  });

  it("treats sorter with null order as clearing order (undefined)", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState),
    );

    act(() => {
      result.current.tableProps.onChange?.(
        { current: 1, pageSize: 25 },
        {},
        { field: "createdAt", order: null },
        {} as any,
      );
    });

    expect(tableState.updateSorting).toHaveBeenCalledWith(
      "createdAt",
      undefined,
    );
  });

  it("supports bulk action helpers based on current selection", () => {
    const onClick = jest.fn() as jest.MockedFunction<(rows: Row[]) => void>;
    const actionDisabled = jest
      .fn()
      .mockReturnValue(false) as jest.MockedFunction<(rows: Row[]) => boolean>;
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        enableSelection: true,
        bulkActions: {
          actions: [
            {
              key: "delete",
              label: "Delete",
              onClick,
              disabled: actionDisabled,
            },
          ],
          getRowKey: (row) => row.id ?? row.key ?? "",
        },
      }),
    );

    // No selection -> disabled
    expect(result.current.getBulkActionProps("delete")).toMatchObject({
      disabled: true,
      loading: false,
    });

    // Select rows
    act(() => {
      result.current.selectionProps!.onChange(["1"], [{ id: "1", name: "A" }]);
    });

    const btnProps = result.current.getBulkActionProps("delete");
    expect(btnProps.disabled).toBe(false);
    expect(btnProps.loading).toBe(false);

    act(() => {
      btnProps.onClick?.();
    });
    expect(onClick).toHaveBeenCalledWith([{ id: "1", name: "A" }]);

    // Unknown action -> disabled
    expect(result.current.getBulkActionProps("missing")).toEqual({
      disabled: true,
      loading: false,
    });
  });

  it("handles empty data source correctly", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        dataSource: [],
        totalRows: 0,
      }),
    );

    expect(result.current.hasData).toBe(false);
    expect(result.current.tableProps.dataSource).toEqual([]);
    if (isPaginationConfig(result.current.tableProps.pagination)) {
      expect(result.current.tableProps.pagination.total).toBe(0);
    }
  });

  it("handles multi-sort scenarios (ignores array sorters)", () => {
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState),
    );

    act(() => {
      // Simulate multi-sort with array sorter
      result.current.tableProps.onChange?.(
        { current: 1, pageSize: 25 },
        {},
        [
          { field: "name", order: "ascend" },
          { field: "createdAt", order: "descend" },
        ],
        {} as any,
      );
    });

    // Should ignore array sorters and not call updateSorting with any field
    expect(tableState.updateSorting).toHaveBeenCalledWith(undefined, undefined);
  });

  it("uses custom getRowKey when provided", () => {
    const customGetRowKey = jest
      .fn()
      .mockReturnValue("custom-key") as jest.MockedFunction<
      (record: Row) => string
    >;
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        getRowKey: customGetRowKey,
      }),
    );

    const testRow = { id: "abc", name: "Test" };
    if (typeof result.current.tableProps.rowKey === "function") {
      result.current.tableProps.rowKey(testRow);
    }

    expect(customGetRowKey).toHaveBeenCalledWith(testRow);
  });

  it("handles bulk action with disabled function", () => {
    const onClick = jest.fn() as jest.MockedFunction<(rows: Row[]) => void>;
    const actionDisabled = jest
      .fn()
      .mockReturnValue(true) as jest.MockedFunction<(rows: Row[]) => boolean>;
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        enableSelection: true,
        bulkActions: {
          actions: [
            {
              key: "delete",
              label: "Delete",
              onClick,
              disabled: actionDisabled,
            },
          ],
          getRowKey: (row) => row.id ?? row.key ?? "",
        },
      }),
    );

    // Select a row
    act(() => {
      result.current.selectionProps!.onChange(["1"], [{ id: "1", name: "A" }]);
    });

    // Action should be disabled due to disabled function returning true
    const btnProps = result.current.getBulkActionProps("delete");
    expect(btnProps.disabled).toBe(true);
    expect(actionDisabled).toHaveBeenCalledWith([{ id: "1", name: "A" }]);
  });

  it("handles bulk action loading state", () => {
    const onClick = jest.fn() as jest.MockedFunction<(rows: Row[]) => void>;
    const tableState = createTableState();
    const { result } = renderHook(() =>
      useAntTable<Row, SortField>(tableState, {
        enableSelection: true,
        bulkActions: {
          actions: [
            {
              key: "save",
              label: "Save",
              onClick,
              loading: true,
            },
          ],
          getRowKey: (row) => row.id ?? row.key ?? "",
        },
      }),
    );

    // Select a row
    act(() => {
      result.current.selectionProps!.onChange(["1"], [{ id: "1", name: "A" }]);
    });

    const btnProps = result.current.getBulkActionProps("save");
    expect(btnProps.loading).toBe(true);
  });

  describe("pagination change detection edge cases", () => {
    it("handles undefined pagination.current without triggering false pagination change", () => {
      const tableState = createTableState({ pageIndex: 1, pageSize: 25 });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        // Simulate pagination object with undefined current but defined pageSize
        result.current.tableProps.onChange?.(
          { current: undefined, pageSize: 25 } as any,
          {},
          { field: "name", order: "ascend" },
          {} as any,
        );
      });

      // Should trigger sorting and filtering updates (not a pagination change)
      expect(tableState.updateSorting).toHaveBeenCalledWith("name", "ascend");
      expect(tableState.updateFilters).toHaveBeenCalledWith({});
    });

    it("handles undefined pagination.pageSize without triggering false pagination change", () => {
      const tableState = createTableState({ pageIndex: 1, pageSize: 25 });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        // Simulate pagination object with defined current but undefined pageSize
        result.current.tableProps.onChange?.(
          { current: 1, pageSize: undefined } as any,
          {},
          { field: "name", order: "ascend" },
          {} as any,
        );
      });

      // Should trigger sorting and filtering updates (not a pagination change)
      expect(tableState.updateSorting).toHaveBeenCalledWith("name", "ascend");
      expect(tableState.updateFilters).toHaveBeenCalledWith({});
    });

    it("handles both pagination.current and pagination.pageSize undefined", () => {
      const tableState = createTableState({ pageIndex: 2, pageSize: 50 });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        // Simulate pagination object with both values undefined
        result.current.tableProps.onChange?.(
          { current: undefined, pageSize: undefined } as any,
          { status: ["active"] },
          {},
          {} as any,
        );
      });

      // Should trigger filtering and sorting updates (not a pagination change)
      expect(tableState.updateFilters).toHaveBeenCalledWith({
        status: ["active"],
      });
      expect(tableState.updateSorting).toHaveBeenCalledWith(
        undefined,
        undefined,
      );
    });

    it("correctly detects actual pagination changes with undefined fallbacks", () => {
      const tableState = createTableState({ pageIndex: 1, pageSize: 25 });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        // Real pagination change: undefined current (defaults to 1) but different pageSize
        result.current.tableProps.onChange?.(
          { current: undefined, pageSize: 50 } as any,
          {},
          {},
          {} as any,
        );
      });

      // Should trigger pagination update because effective pageSize changed (25 → 50)
      expect(tableState.updatePagination).toHaveBeenCalledWith(1, 50);
      expect(tableState.updateFilters).not.toHaveBeenCalled();
      expect(tableState.updateSorting).not.toHaveBeenCalled();
    });

    it("correctly detects actual pagination changes when current is undefined but effective page differs", () => {
      const tableState = createTableState({ pageIndex: 3, pageSize: 25 });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        // undefined current defaults to tableState.pageIndex (3), but we're comparing against 3
        // This should NOT be a pagination change
        result.current.tableProps.onChange?.(
          { current: undefined, pageSize: 25 } as any,
          {},
          { field: "name", order: "ascend" },
          {} as any,
        );
      });

      // Should trigger sorting update (not a pagination change)
      expect(tableState.updateSorting).toHaveBeenCalledWith("name", "ascend");
    });

    it("handles edge case where tableState values are also undefined", () => {
      // Edge case: tableState itself has undefined values
      const tableState = createTableState({
        pageIndex: undefined as any,
        pageSize: undefined as any,
      });
      const { result } = renderHook(() =>
        useAntTable<Row, SortField>(tableState),
      );

      act(() => {
        result.current.tableProps.onChange?.(
          { current: undefined, pageSize: undefined } as any,
          {},
          {},
          {} as any,
        );
      });

      // Should handle gracefully and trigger appropriate updates
      expect(tableState.updateFilters).toHaveBeenCalledWith({});
      expect(tableState.updateSorting).toHaveBeenCalledWith(
        undefined,
        undefined,
      );
    });
  });
});
