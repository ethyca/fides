/**
 * Pagination state interface
 */
export interface PaginationState {
  pageIndex: number;
  pageSize: number;
}

/**
 * Cursor pagination state interface
 */
export interface CursorPaginationState {
  cursor_start?: string;
  cursor_end?: string;
  pageSize: number;
}

/**
 * Configuration for pagination (standalone or table)
 */
export interface PaginationConfig {
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  showSizeChanger?: boolean;
  pageQueryKey?: string;
  sizeQueryKey?: string;
  disableUrlState?: boolean;
}

/**
 * Updates for pagination URL state
 */
export interface PaginationQueryParams {
  page?: number | null;
  size?: number | null;
}

/**
 * Updates for cursor pagination URL state
 */
export interface CursorPaginationQueryParams {
  cursor?: string | null;
  size?: number | null;
}
