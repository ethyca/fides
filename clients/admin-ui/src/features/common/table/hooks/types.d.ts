import { AntFilterValue as FilterValue } from "fidesui";

/**
 * Base interface for table state that can be synchronized with URL
 */
export interface TableState {
  // Pagination
  pageIndex: number;
  pageSize: number;

  // Sorting
  sortField?: string;
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
export interface SortingConfig {
  defaultSortField?: string;
  defaultSortOrder?: "ascend" | "descend";
  allowMultiSort?: boolean;
}

/**
 * Base configuration for table state management
 */
export interface TableStateConfig {
  // URL synchronization
  urlSync?: TableUrlSyncConfig;

  // Default values
  pagination?: PaginationConfig;
  sorting?: SortingConfig;

  // Callbacks
  onStateChange?: (state: TableState) => void;
}

/**
 * Generic server table configuration
 */
export interface ServerTableConfig<TData = unknown> {
  queryKey: string | string[];
  queryFn: (params: TableState & Record<string, unknown>) => Promise<{
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
  selectedRowsMap: Map<string, TData>;
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
