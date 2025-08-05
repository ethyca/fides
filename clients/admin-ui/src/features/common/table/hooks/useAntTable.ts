import {
  AntFilterValue as FilterValue,
  AntSorterResult as SorterResult,
  AntTablePaginationConfig as TablePaginationConfig,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { BulkActionsConfig, SelectionState } from "./types";

/**
 * Configuration for Ant Design table integration
 */
export interface AntTableConfig<TData = any> {
  // Row selection
  enableSelection?: boolean;
  getRowKey?: (record: TData) => string;

  // Bulk actions
  bulkActions?: BulkActionsConfig<TData>;

  // Table behavior
  enableSorting?: boolean;
  enableFiltering?: boolean;

  // Loading states
  isLoading?: boolean;
  isFetching?: boolean;

  // Data
  dataSource?: TData[];
  totalRows?: number;
}

/**
 * Hook for Ant Design table integration with table state management
 *
 * @param tableState - Table state from useTableState or useServerTable
 * @param config - Ant Design specific configuration
 * @returns Ant Design table props and utilities
 *
 * @example
 * ```tsx
 * const serverTable = useServerTable(serverConfig);
 * const {
 *   tableProps,
 *   selectionProps,
 *   selectedRows,
 *   resetSelections
 * } = useAntTable(serverTable, {
 *   enableSelection: true,
 *   getRowKey: (record) => record.id,
 *   dataSource: serverTable.data?.items,
 *   totalRows: serverTable.totalRows
 * });
 *
 * return <Table {...tableProps} rowSelection={selectionProps} />;
 * ```
 */
export const useAntTable = <TData = any>(
  tableState: {
    pageIndex: number;
    pageSize: number;
    sortField?: string;
    sortOrder?: "ascend" | "descend";
    columnFilters: Record<string, FilterValue | null>;
    updatePagination: (pageIndex: number, pageSize?: number) => void;
    updateSorting: (
      sortField?: string,
      sortOrder?: "ascend" | "descend",
    ) => void;
    updateFilters: (filters: Record<string, any>) => void;
    paginationConfig?: {
      pageSizeOptions: number[];
      showSizeChanger: boolean;
    };
  },
  config: AntTableConfig<TData> = {},
) => {
  const {
    enableSelection = false,
    getRowKey = (record: any) => record.id || record.key,
    bulkActions,
    enableSorting = true,
    enableFiltering = true,
    isLoading = false,
    isFetching = false,
    dataSource = [],
    totalRows = 0,
  } = config;

  // Selection state management
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRowsMap, setSelectedRowsMap] = useState<Map<string, TData>>(
    new Map(),
  );

  const resetSelections = useCallback(() => {
    setSelectedRowKeys([]);
    setSelectedRowsMap(new Map());
  }, []);

  const selectionState: SelectionState<TData> = {
    selectedRowKeys,
    selectedRowsMap,
    resetSelections,
  };

  // Selection props for Ant Design Table
  const selectionProps = useMemo(() => {
    if (!enableSelection) {
      return undefined;
    }

    return {
      selectedRowKeys,
      onChange: (newSelectedRowKeys: React.Key[], newSelectedRows: TData[]) => {
        setSelectedRowKeys(newSelectedRowKeys);

        // Update the map with current page selections
        const newMap = new Map(selectedRowsMap);

        // Remove deselected items from current page
        dataSource.forEach((item) => {
          const key = getRowKey(item);
          if (!newSelectedRowKeys.includes(key)) {
            newMap.delete(key);
          }
        });

        // Add newly selected items
        newSelectedRows.forEach((row) => {
          const key = getRowKey(row);
          newMap.set(key, row);
        });

        setSelectedRowsMap(newMap);
      },
    };
  }, [
    enableSelection,
    selectedRowKeys,
    selectedRowsMap,
    dataSource,
    getRowKey,
  ]);

  // Update selectedRowKeys to only show current page selections when data changes
  useMemo(() => {
    if (dataSource.length > 0) {
      const currentPageSelectedKeys = dataSource
        .filter((item) => selectedRowsMap.has(getRowKey(item)))
        .map((item) => getRowKey(item));
      setSelectedRowKeys(currentPageSelectedKeys);
    }
  }, [dataSource, selectedRowsMap, getRowKey]);

  // Table change handler
  const handleTableChange = useCallback(
    (
      pagination: TablePaginationConfig,
      filters: Record<string, FilterValue | null>,
      sorter: SorterResult<TData> | SorterResult<TData>[],
    ) => {
      // Handle pagination
      const newPageIndex = pagination.current || 1;
      const newPageSize = pagination.pageSize || tableState.pageSize;

      // Check if this is just a pagination change
      const isPaginationChange =
        newPageIndex !== tableState.pageIndex ||
        newPageSize !== tableState.pageSize;

      if (
        isPaginationChange &&
        JSON.stringify(filters) === JSON.stringify(tableState.columnFilters) &&
        (!sorter ||
          Array.isArray(sorter) ||
          (sorter.field === tableState.sortField &&
            sorter.order === tableState.sortOrder))
      ) {
        // Only pagination changed
        tableState.updatePagination(newPageIndex, newPageSize);
      } else {
        // Other changes occurred, reset to first page
        tableState.updatePagination(1, newPageSize);
      }

      // Handle filtering
      if (
        enableFiltering &&
        JSON.stringify(filters) !== JSON.stringify(tableState.columnFilters)
      ) {
        tableState.updateFilters(filters || {});
      }

      // Handle sorting
      if (enableSorting && sorter && !Array.isArray(sorter)) {
        const newSortField = sorter.field as string;
        const newSortOrder = sorter.order;

        if (
          newSortField !== tableState.sortField ||
          newSortOrder !== tableState.sortOrder
        ) {
          tableState.updateSorting(newSortField, newSortOrder || undefined);
        }
      }
    },
    [tableState, enableFiltering, enableSorting],
  );

  // Pagination configuration
  const paginationProps = useMemo(
    () => ({
      current: tableState.pageIndex,
      pageSize: tableState.pageSize,
      total: totalRows,
      showSizeChanger: tableState.paginationConfig?.showSizeChanger ?? true,
      pageSizeOptions: tableState.paginationConfig?.pageSizeOptions?.map(
        String,
      ) ?? ["10", "25", "50", "100"],
      showQuickJumper: true,
      showTotal: (total: number, range: [number, number]) =>
        `${range[0]}-${range[1]} of ${total} items`,
    }),
    [
      tableState.pageIndex,
      tableState.pageSize,
      totalRows,
      tableState.paginationConfig,
    ],
  );

  // Main table props
  const tableProps = {
    dataSource,
    loading: isLoading || isFetching,
    pagination: paginationProps,
    onChange: handleTableChange,
    rowKey: getRowKey,
    scroll: { x: "max-content", scrollToFirstRowOnChange: true },
    size: "small" as const,
    bordered: true,
  };

  // Selected data helpers
  const selectedRows = Array.from(selectedRowsMap.values());
  const selectedKeys = Array.from(selectedRowsMap.keys());
  const hasSelectedRows = selectedRows.length > 0;

  // Bulk actions helpers
  const getBulkActionProps = useCallback(
    (actionKey: string) => {
      const action = bulkActions?.actions.find((a) => a.key === actionKey);
      if (!action) {
        return { disabled: true, loading: false };
      }

      return {
        disabled:
          !hasSelectedRows ||
          (action.disabled ? action.disabled(selectedRows) : false),
        loading: action.loading || false,
        onClick: () => action.onClick(selectedRows),
      };
    },
    [bulkActions, hasSelectedRows, selectedRows],
  );

  return {
    // Main table props
    tableProps,

    // Selection
    selectionProps,
    selectionState,
    selectedRows,
    selectedKeys,
    hasSelectedRows,
    resetSelections,

    // Bulk actions
    getBulkActionProps,

    // Utilities
    isLoadingOrFetching: isLoading || isFetching,
    hasData: dataSource.length > 0,
  };
};
