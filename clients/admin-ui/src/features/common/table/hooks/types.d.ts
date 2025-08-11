import { AntFilterValue as FilterValue } from "fidesui";

/**
 * Sort order type for table sorting
 */
export type SortOrder = "ascend" | "descend";

/**
 * Base interface for table state that can be synchronized with URL
 */
export interface TableState<TSortField extends string = string> {
  // Pagination
  pageIndex: number;
  pageSize: number;

  // Sorting
  sortField?: TSortField;
  sortOrder?: SortOrder;

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
  defaultSortOrder?: SortOrder;
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

/**
 * Type for URL query state updates based on enabled features
 */
type QueryStateUpdates = {
  page?: number | null;
  size?: number | null;
  sortField?: string | null;
  sortOrder?: string | null;
  filters?: Record<string, FilterValue | null> | null;
  search?: string | null;
};
