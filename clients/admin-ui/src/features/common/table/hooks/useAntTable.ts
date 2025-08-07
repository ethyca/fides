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

  // Loading states
  isLoading?: boolean;
  isFetching?: boolean;

  // Data
  dataSource?: TData[];
  totalRows?: number;

  // Pagination overrides (optional - defaults to tableState values)
  currentPage?: number;
  pageSize?: number;

  // Custom table props
  customTableProps?: any;
}

/**
 * Hook for Ant Design table integration with table state management
 *
 * @param tableState - Table state from useTableState hook
 * @param config - Ant Design specific configuration
 * @returns Ant Design table props and utilities
 *
 * @example
 * ```tsx
 * const tableState = useTableState<MyColumnKeys>();
 * const { data, isLoading } = useGetMyDataQuery(tableState.queryParams);
 *
 * const {
 *   tableProps,
 *   selectionProps,
 *   selectedRows,
 *   resetSelections
 * } = useAntTable(tableState, {
 *   enableSelection: true,
 *   getRowKey: (record) => record.id,
 *   dataSource: data?.items || [],
 *   totalRows: data?.total || 0,
 *   isLoading
 * });
 *
 * return <Table {...tableProps} rowSelection={selectionProps} />;
 * ```
 */
export const useAntTable = <TData = any, TSortField extends string = string>(
  tableState: {
    pageIndex: number;
    pageSize: number;
    sortField?: TSortField;
    sortOrder?: "ascend" | "descend";
    columnFilters: Record<string, FilterValue | null>;
    updatePagination: (pageIndex: number, pageSize?: number) => void;
    updateSorting: (
      sortField?: TSortField,
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
    getRowKey: providedGetRowKey,
    bulkActions,
    isLoading = false,
    isFetching = false,
    dataSource = [],
    totalRows = 0,
    currentPage,
    pageSize: configPageSize,
    customTableProps = {},
  } = config;

  // Memoize the getRowKey function to prevent recreation
  const getRowKey = useMemo(
    () => providedGetRowKey || ((record: any) => record.id || record.key),
    [providedGetRowKey],
  );

  // Selection state management (simplified to match original working pattern)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRows, setSelectedRows] = useState<TData[]>([]);

  const resetSelections = useCallback(() => {
    setSelectedRowKeys([]);
    setSelectedRows([]);
  }, []);

  const selectionState: SelectionState<TData> = useMemo(
    () => ({
      selectedRowKeys,
      selectedRows,
      resetSelections,
    }),
    [selectedRowKeys, selectedRows, resetSelections],
  );

  // Selection props for Ant Design Table (simplified to match original working pattern)
  const selectionProps = useMemo(() => {
    if (!enableSelection) {
      return undefined;
    }

    return {
      selectedRowKeys,
      onChange: (newSelectedRowKeys: React.Key[], newSelectedRows: TData[]) => {
        setSelectedRowKeys(newSelectedRowKeys);
        setSelectedRows(newSelectedRows);
      },
    };
  }, [enableSelection, selectedRowKeys]);

  // Table change handler
  const handleTableChange = useCallback(
    (
      pagination: TablePaginationConfig,
      filters: Record<string, FilterValue | null>,
      sorter: SorterResult<TData> | SorterResult<TData>[],
    ) => {
      // Check if this is just a pagination change (page or pageSize changed)
      const isPaginationChange =
        pagination.current !== tableState.pageIndex ||
        pagination.pageSize !== tableState.pageSize;

      // Handle pagination with tableState
      if (isPaginationChange) {
        tableState.updatePagination(
          pagination.current || 1,
          pagination.pageSize,
        );
      } else {
        tableState.updatePagination(1); // Reset to page 1 for sorting/filtering changes
        // Only update filters when it's not a pagination change
        tableState.updateFilters(filters || {});
      }

      // Handle sorting with tableState (only if sorting actually changed)
      const newSortField =
        sorter && !Array.isArray(sorter)
          ? (sorter.field as TSortField)
          : undefined;
      const newSortOrder =
        sorter && !Array.isArray(sorter) && sorter.order !== null
          ? sorter.order
          : undefined;

      // Only update sorting if this is not just a pagination change
      if (!isPaginationChange) {
        tableState.updateSorting(newSortField, newSortOrder);
      }
    },
    [tableState],
  );

  // Pagination configuration
  const paginationProps = useMemo(
    () => ({
      current: currentPage ?? tableState.pageIndex,
      pageSize: configPageSize ?? tableState.pageSize,
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
      currentPage,
      tableState.pageIndex,
      configPageSize,
      tableState.pageSize,
      totalRows,
      tableState.paginationConfig,
    ],
  );

  // Main table props (memoized)
  const tableProps = useMemo(
    () => ({
      dataSource,
      loading: isLoading || isFetching,
      pagination: paginationProps,
      onChange: handleTableChange,
      rowKey: getRowKey,
      scroll: { x: "max-content", scrollToFirstRowOnChange: true },
      size: "small" as const,
      bordered: true,
      ...customTableProps,
    }),
    [
      dataSource,
      isLoading,
      isFetching,
      paginationProps,
      handleTableChange,
      getRowKey,
      customTableProps,
    ],
  );

  // Selected data helpers (simplified to match original working pattern)
  const selectedKeys = useMemo(
    () => selectedRowKeys.map(String),
    [selectedRowKeys],
  );
  const hasSelectedRows = useMemo(
    () => selectedRows.length > 0,
    [selectedRows],
  );

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

  return useMemo(
    () => ({
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
    }),
    [
      tableProps,
      selectionProps,
      selectionState,
      selectedRows,
      selectedKeys,
      hasSelectedRows,
      resetSelections,
      getBulkActionProps,
      isLoading,
      isFetching,
      dataSource.length,
    ],
  );
};
