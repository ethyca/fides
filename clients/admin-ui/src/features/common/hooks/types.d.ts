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
export interface SortingState<TSortKey extends string = string> {
  sortKey?: TSortKey;
  sortOrder?: SortOrder;
}

/**
 * Configuration for table sorting
 */
export interface SortingConfig<TSortKey extends string = string> {
  defaultSortKey?: TSortKey;
  defaultSortOrder?: SortOrder;
  allowMultiSort?: boolean;
  validColumns?: readonly TSortKey[];
  onSortingChange?: (state: SortingState<TSortKey>) => void;
}

/**
 * Updates for sorting URL state
 */
export interface SortingQueryParams {
  sortKey?: string | null;
  sortOrder?: SortOrder | null;
}

/**
 * Search state interface
 */
export interface SearchState {
  searchQuery?: string;
}

/**
 * Configuration for search (standalone or table)
 */
export interface SearchConfig {
  defaultSearchQuery?: string;
  onSearchChange?: (state: SearchState) => void;
}

/**
 * Updates for search URL state
 */
export interface SearchQueryParams {
  search?: string | null;
}
