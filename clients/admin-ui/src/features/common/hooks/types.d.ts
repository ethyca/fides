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
 * TSortKey should be constrained to specific column key enums for type safety
 *
 * Example usage:
 * - Define an enum: `enum MyColumnKeys { NAME = "name", TYPE = "type" }`
 * - Use with hook: `useSorting<MyColumnKeys>(config)`
 */
export interface SortingState<TSortKey extends string = string> {
  sortKey?: TSortKey;
  sortOrder?: SortOrder;
}

/**
 * Configuration for table sorting
 * TSortKey should be constrained to specific column key enums for type safety
 *
 * @example
 * ```tsx
 * enum MyColumnKeys {
 *   NAME = "name",
 *   TYPE = "type",
 *   CREATED_AT = "createdAt"
 * }
 *
 * const config: SortingConfig<MyColumnKeys> = {
 *   defaultSortKey: MyColumnKeys.NAME,
 *   defaultSortOrder: 'ascend',
 *   validColumns: Object.values(MyColumnKeys),
 *   onSortingChange: (state) => console.log('Sorting changed:', state)
 * };
 *
 * const sorting = useSorting<MyColumnKeys>(config);
 * ```
 */
export interface SortingConfig<TSortKey extends string = string> {
  /** Default column to sort by when no sorting is active */
  defaultSortKey?: TSortKey;
  /** Default sort direction when no sorting is active */
  defaultSortOrder?: SortOrder;
  /**
   * Array of valid column keys for URL validation.
   * When provided, uses parseAsStringEnum to enforce that only these values
   * can be parsed from URL parameters. Invalid values will be rejected.
   * Recommended for all table implementations.
   */
  validColumns?: readonly TSortKey[];
  /** Callback fired when sorting state changes */
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
