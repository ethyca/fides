import type { AntFilterValue as FilterValue } from "fidesui";

import type {
  PaginationConfig,
  PaginationState,
  SortingConfig,
  SortOrder,
} from "../../hooks/types";

/**
 * Base interface for table state that can be synchronized with URL
 */
export interface TableState<TSortField extends string = string>
  extends PaginationState {
  sortField?: TSortField;
  sortOrder?: SortOrder;
  columnFilters?: Record<string, FilterValue | null>;
  searchQuery?: string;
  paginationConfig?: PaginationConfig;
}

export interface TableStateWithHelpers<TSortField extends string = string>
  extends TableState<TSortField> {
  updatePagination: (pageIndex: number, pageSize?: number) => void;
  updateSorting: (sortField?: TSortField, sortOrder?: SortOrder) => void;
  updateFilters: (filters: Record<string, FilterValue | null>) => void;
  resetState: () => void;
  updateSearch: (searchQuery: string) => void;
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
 * Pagination updates are handled separately by PaginationUpdates
 * Sorting updates are handled separately by SortingUpdates
 */
export interface QueryStateUpdates {
  filters?: Record<string, FilterValue | null> | null;
  search?: string | null;
}
