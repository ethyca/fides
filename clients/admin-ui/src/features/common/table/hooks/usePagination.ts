import { parseAsInteger, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import {
  DEFAULT_PAGE_INDEX,
  DEFAULT_PAGE_SIZE,
  DEFAULT_PAGE_SIZES,
} from "../constants";
import type {
  PaginationConfig,
  PaginationState,
  PaginationUpdates,
} from "./types";

/**
 * NuQS parsers for pagination state - synced to URL
 */
const createPaginationParsers = (defaults: { pageSize?: number } = {}) => ({
  page: parseAsInteger.withDefault(DEFAULT_PAGE_INDEX),
  size: parseAsInteger.withDefault(defaults.pageSize ?? DEFAULT_PAGE_SIZE),
});

/**
 * Custom hook for managing pagination state with URL synchronization
 *
 * This hook manages pagination state (current page and page size) and
 * synchronizes it with URL query parameters using NuQS. The URL query parameters
 * are the single source of truth for pagination state.
 *
 * Can be used standalone for any paginated component (not just tables) or
 * consumed by table state management hooks.
 *
 * @param config - Configuration for pagination state management
 * @returns Pagination state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const pagination = usePagination();
 *
 * // With custom default values
 * const pagination = usePagination({
 *   defaultPageSize: 50,
 *   pageSizeOptions: [25, 50, 100, 200]
 * });
 *
 * // With state change callback
 * const pagination = usePagination({
 *   onPaginationChange: (state) => console.log('Pagination changed:', state)
 * });
 *
 * // Use with Ant Pagination component
 * <Pagination
 *   current={pagination.pageIndex}
 *   pageSize={pagination.pageSize}
 *   total={totalItems}
 *   showSizeChanger={pagination.showSizeChanger}
 *   pageSizeOptions={pagination.pageSizeOptions.map(String)}
 *   onChange={pagination.updatePagination}
 *   onShowSizeChange={pagination.updatePagination}
 * />
 * ```
 */
export const usePagination = (config: PaginationConfig = {}) => {
  const {
    defaultPageSize = DEFAULT_PAGE_SIZE,
    pageSizeOptions = DEFAULT_PAGE_SIZES,
    showSizeChanger = true,
    onPaginationChange,
  } = config;

  // Create parsers for pagination state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    const createdParsers = createPaginationParsers({
      pageSize: defaultPageSize,
    });
    return createdParsers;
  }, [defaultPageSize]);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state (URL is the single source of truth)
  const currentState: PaginationState = useMemo(
    () => ({
      pageIndex: queryState.page ?? DEFAULT_PAGE_INDEX,
      pageSize: queryState.size ?? defaultPageSize,
    }),
    [queryState, defaultPageSize],
  );

  // Update functions that update query state (URL is the single source of truth)
  const updatePagination = useCallback(
    (pageIndex: number, pageSize?: number) => {
      const newPageIndex =
        pageSize !== undefined && pageSize !== currentState.pageSize
          ? DEFAULT_PAGE_INDEX // Reset to first page when changing page size
          : pageIndex;

      const updates: PaginationUpdates = { page: newPageIndex };
      if (pageSize !== undefined) {
        updates.size = pageSize;
      }
      setQueryState(updates);
    },
    [setQueryState, currentState.pageSize],
  );

  const resetPagination = () => {
    // Reset pagination URL state
    setQueryState({
      page: DEFAULT_PAGE_INDEX,
      size: defaultPageSize,
    });
  };

  // Call onPaginationChange when state changes
  useEffect(() => {
    if (onPaginationChange) {
      onPaginationChange(currentState);
    }
  }, [currentState, onPaginationChange]);

  return {
    // Current state
    ...currentState,

    // Update functions
    updatePagination,
    resetPagination,

    // Configuration for components
    pageSizeOptions,
    showSizeChanger,

    // Ant Design pagination props
    paginationProps: {
      current: currentState.pageIndex,
      pageSize: currentState.pageSize,
      showSizeChanger,
      pageSizeOptions: pageSizeOptions.map(String),
      showQuickJumper: true,
      showTotal: (total: number, range: [number, number]) =>
        `${range[0]}-${range[1]} of ${total} items`,
      onChange: updatePagination,
      onShowSizeChange: updatePagination,
    },
  };
};
