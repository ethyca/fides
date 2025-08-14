/**
 * Pagination state interface
 */
export interface PaginationState {
  pageIndex: number;
  pageSize: number;
}

/**
 * Configuration for pagination (standalone or table)
 */
export interface PaginationConfig {
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  showSizeChanger?: boolean;
  onPaginationChange?: (state: PaginationState) => void;
}

/**
 * Updates for pagination URL state
 */
export interface PaginationQueryParams {
  page?: number | null;
  size?: number | null;
}

/**
 * Sort order type for table sorting
 */
export type SortOrder = "ascend" | "descend";

/**
 * Sorting state interface
 */
export interface SortingState<TSortField extends string = string> {
  sortField?: TSortField;
  sortOrder?: SortOrder;
}

/**
 * Configuration for table sorting
 */
export interface SortingConfig<TSortField extends string = string> {
  defaultSortField?: TSortField;
  defaultSortOrder?: SortOrder;
  allowMultiSort?: boolean;
  onSortingChange?: (state: SortingState<TSortField>) => void;
}

/**
 * Updates for sorting URL state
 */
export interface SortingQueryParams {
  sortField?: string | null;
  sortOrder?: SortOrder | null;
}
