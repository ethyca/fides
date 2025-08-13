import { AntFilterValue as FilterValue } from "fidesui";
import { parseAsJson, parseAsString, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import type {
  QueryStateUpdates,
  SortOrder,
  TableState,
  TableStateConfig,
} from "./types";
import { usePagination } from "./usePagination";

/**
 * NuQS parsers for table state - filtering, sorting, and search features synced to URL
 * Pagination is handled by the usePagination hook
 */
const createTableParsers = () => ({
  sortField: parseAsString.withDefault(""),
  sortOrder: parseAsString.withDefault(""),
  filters: parseAsJson(
    (value: unknown) => value as Record<string, FilterValue | null>,
  ).withDefault({}),
  search: parseAsString.withDefault(""),
});

/**
 * Custom hook for managing table state with URL synchronization
 *
 * This hook manages all table features (pagination, sorting, filtering, search) and
 * synchronizes them with URL query parameters using NuQS. The URL query parameters
 * are the single source of truth for table state.
 *
 * @param config - Configuration for table state management
 * @returns Table state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const tableState = useTableState();
 *
 * // With custom default values
 * const tableState = useTableState({
 *   pagination: { defaultPageSize: 50 },
 *   sorting: { defaultSortField: 'name', defaultSortOrder: 'ascend' }
 * });
 *
 * // With state change callback
 * const tableState = useTableState({
 *   onStateChange: (state) => console.log('Table state changed:', state)
 * });
 * ```
 */
export const useTableState = <TSortField extends string = string>(
  config: TableStateConfig<TSortField> = {},
) => {
  const {
    pagination: paginationConfig = {},
    sorting: sortingConfig = {},
    onStateChange,
  } = config;

  const { defaultSortField, defaultSortOrder } = sortingConfig;

  // Use the standalone pagination hook
  const {
    pageIndex,
    pageSize,
    resetPagination,
    updatePagination,
    pageSizeOptions,
    showSizeChanger,
  } = usePagination(paginationConfig);

  // Create parsers for non-pagination table state features
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => createTableParsers(), []);

  // Use NuQS for URL state management (excluding pagination)
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state and pagination hook (URL is the single source of truth)
  const currentState: TableState<TSortField> = useMemo(() => {
    const state = {
      pageIndex,
      pageSize,
      sortField: (queryState.sortField as TSortField) || defaultSortField, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      sortOrder:
        (queryState.sortOrder as SortOrder | undefined) || defaultSortOrder, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      columnFilters: queryState.filters ?? {},
      searchQuery: queryState.search || undefined, // Convert empty string to undefined
    };

    return state;
  }, [queryState, pageIndex, pageSize, defaultSortField, defaultSortOrder]);

  // Update functions that update query state (URL is the single source of truth)
  // Pagination updates are handled by the pagination hook

  const updateSorting = useCallback(
    (sortField?: TSortField, sortOrder?: SortOrder) => {
      setQueryState({
        sortField: sortField ? String(sortField) : null,
        sortOrder: sortOrder ?? null,
      });
      resetPagination(); // Reset to first page when sorting changes
    },
    [setQueryState, resetPagination],
  );

  const updateFilters = useCallback(
    (filters: Record<string, FilterValue | null>) => {
      // Clean up filters by removing null/undefined values before syncing to URL
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value != null),
      );
      setQueryState({
        filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : null, // Use null to remove from URL when empty
      });
      resetPagination(); // Reset to first page when filters change
    },
    [setQueryState, resetPagination],
  );

  const updateSearch = useCallback(
    (searchQuery?: string) => {
      setQueryState({
        search: searchQuery || null,
      });
      resetPagination(); // Reset to first page when search changes
    },
    [setQueryState, resetPagination],
  );

  const resetState = useCallback(() => {
    // Reset all URL state
    const urlUpdates: QueryStateUpdates = {
      sortField: null,
      sortOrder: null,
      filters: null,
      search: null,
    };
    setQueryState(urlUpdates);
    resetPagination();
  }, [setQueryState, resetPagination]);

  // Call onStateChange when state changes
  useEffect(() => {
    if (onStateChange) {
      onStateChange(currentState);
    }
  }, [currentState, onStateChange]);

  return {
    // Current state
    state: currentState,

    // Pagination (delegated to pagination hook)
    pageIndex: currentState.pageIndex,
    pageSize: currentState.pageSize,
    updatePagination,

    // Sorting
    sortField: currentState.sortField,
    sortOrder: currentState.sortOrder,
    updateSorting,

    // Filtering
    columnFilters: currentState.columnFilters,
    updateFilters,

    // Search
    searchQuery: currentState.searchQuery,
    updateSearch,

    // Reset
    resetState,

    // Configuration (delegated to pagination hook)
    paginationConfig: {
      pageSizeOptions,
      showSizeChanger,
    },
  };
};
