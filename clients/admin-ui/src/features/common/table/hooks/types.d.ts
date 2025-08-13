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
 * URL synchronization is now always enabled for all features
 */
export interface TableStateConfig<TSortField extends string = string> {
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
 * Configuration for Ant Design table integration
 */
export interface AntTableHookConfig<TData> {
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
  customTableProps?: Partial<TableProps<TData>>;
}

/**
 * Type for URL query state updates based on enabled features
 */
export interface QueryStateUpdates {
  page?: number | null;
  size?: number | null;
  sortField?: string | null;
  sortOrder?: string | null;
  filters?: Record<string, FilterValue | null> | null;
  search?: string | null;
}
