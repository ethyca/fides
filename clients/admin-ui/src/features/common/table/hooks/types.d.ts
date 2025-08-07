import { AntFilterValue as FilterValue } from "fidesui";

/**
 * Base interface for table state that can be synchronized with URL
 */
export interface TableState<TSortField extends string = string> {
  // Pagination
  pageIndex: number;
  pageSize: number;

  // Sorting
  sortField?: TSortField;
  sortOrder?: "ascend" | "descend";

  // Filtering
  columnFilters: Record<string, FilterValue | null>;
  searchQuery?: string;

  // Selection (optional, not synced to URL by default)
  selectedRowKeys?: React.Key[];
}

/**
 * Configuration for which table state should be synced to URL
 */
export interface TableUrlSyncConfig {
  pagination?: boolean;
  sorting?: boolean;
  filtering?: boolean;
  search?: boolean;
}

/**
 * Configuration for table pagination
 */
export interface PaginationConfig {
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  showSizeChanger?: boolean;
}

/**
 * Configuration for table sorting
 */
export interface SortingConfig<TSortField extends string = string> {
  defaultSortField?: TSortField;
  defaultSortOrder?: "ascend" | "descend";
  allowMultiSort?: boolean;
}

/**
 * Base configuration for table state management
 */
export interface TableStateConfig<TSortField extends string = string> {
  // URL synchronization
  urlSync?: TableUrlSyncConfig;

  // Default values
  pagination?: PaginationConfig;
  sorting?: SortingConfig<TSortField>;

  // Callbacks
  onStateChange?: (state: TableState<TSortField>) => void;
}

/**
 * Generic server table configuration
 */
export interface ServerTableConfig<
  TData = unknown,
  TSortField extends string = string,
> {
  queryKey: string | string[];
  queryFn: (
    params: TableState<TSortField> & Record<string, unknown>,
  ) => Promise<{
    items: TData[];
    total: number;
    page: number;
    pages: number;
  }>;
  additionalParams?: Record<string, unknown>;
  enabled?: boolean;
}

/**
 * Result from server table hook
 */
export interface ServerTableResult<TData = unknown> {
  data?: {
    items: TData[];
    total: number;
    page: number;
    pages: number;
  };
  isLoading: boolean;
  isFetching: boolean;
  error?: unknown;
  refetch: () => void;
}

/**
 * Selection state management
 */
export interface SelectionState<TData = unknown> {
  selectedRowKeys: React.Key[];
  selectedRows: TData[];
  resetSelections: () => void;
}

/**
 * Bulk actions configuration
 */
export interface BulkActionsConfig<TData = unknown> {
  actions: Array<{
    key: string;
    label: string;
    onClick: (selectedRows: TData[]) => void | Promise<void>;
    disabled?: (selectedRows: TData[]) => boolean;
    loading?: boolean;
  }>;
  getRowKey: (row: TData) => string;
}
