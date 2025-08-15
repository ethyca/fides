import { AntFilterValue as FilterValue } from "fidesui";
import { parseAsJson, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import { type SortOrder, usePagination, useSearch, useSorting } from "../../hooks";
import type {
  QueryStateUpdates,
  TableState,
  TableStateConfig,
  TableStateWithHelpers,
} from "./types";

/**
 * NuQS parsers for table state - filtering features synced to URL
 * Pagination is handled by the usePagination hook
 * Sorting is handled by the useSorting hook
 * Search is handled by the useSearch hook
 */
const createTableParsers = () => {
  return {
    filters: parseAsJson(
      (value: unknown) => value as Record<string, FilterValue | null>,
    ).withDefault({}),
  };
};

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
    search: searchConfig = {},
    onStateChange,
  } = config;

  // Use the standalone pagination hook
  const {
    pageIndex,
    pageSize,
    resetPagination,
    updatePagination,
    pageSizeOptions,
    showSizeChanger,
  } = usePagination(paginationConfig);

  // Use the standalone sorting hook
  const {
    sortField,
    sortOrder,
    updateSorting: updateSortingOnly,
    resetSorting,
  } = useSorting(sortingConfig);

  // Use the standalone search hook
  const {
    searchQuery,
    updateSearch: updateSearchOnly,
    resetSearch,
  } = useSearch(searchConfig);

  // Create parsers for non-pagination table state features
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => createTableParsers(), []);

  // Use NuQS for URL state management (excluding pagination)
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state, pagination hook, sorting hook, and search hook (URL is the single source of truth)
  const currentState: TableState<TSortField> = useMemo(() => {
    const state = {
      pageIndex,
      pageSize,
      sortField,
      sortOrder,
      columnFilters: queryState.filters ?? {},
      searchQuery,
    };

    return state;
  }, [queryState, pageIndex, pageSize, sortField, sortOrder, searchQuery]);

  // Update functions that update query state (URL is the single source of truth)
  // Pagination updates are handled by the pagination hook
  // Sorting updates are handled by the sorting hook
  // Search updates are handled by the search hook

  const updateSorting = useCallback(
    (sf?: TSortField, so?: SortOrder) => {
      updateSortingOnly(sf, so);
      resetPagination(); // Reset to first page when sorting changes
    },
    [updateSortingOnly, resetPagination],
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
      updateSearchOnly(searchQuery);
      resetPagination(); // Reset to first page when search changes
    },
    [updateSearchOnly, resetPagination],
  );

  const resetState = useCallback(() => {
    // Reset all URL state
    const urlUpdates: QueryStateUpdates = {
      filters: null,
    };
    setQueryState(urlUpdates);
    resetPagination();
    resetSorting();
    resetSearch();
  }, [setQueryState, resetPagination, resetSorting, resetSearch]);

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

    // Sorting (delegated to sorting hook)
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
  } as TableStateWithHelpers<TSortField>;
};
