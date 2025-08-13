import { AntFilterValue as FilterValue, PAGE_SIZES } from "fidesui";
import {
  parseAsInteger,
  parseAsJson,
  parseAsString,
  useQueryStates,
} from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import type {
  QueryStateUpdates,
  SortOrder,
  TableState,
  TableStateConfig,
} from "./types";

/**
 * Default configuration values
 */
const DEFAULT_PAGE_SIZE = PAGE_SIZES[0];
const DEFAULT_PAGE_INDEX = 1;

/**
 * NuQS parsers for table state - all features are synced to URL
 */
const createTableParsers = (defaults: { pageSize?: number } = {}) => ({
  page: parseAsInteger.withDefault(DEFAULT_PAGE_INDEX),
  size: parseAsInteger.withDefault(defaults.pageSize ?? DEFAULT_PAGE_SIZE),
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

  const {
    defaultPageSize = DEFAULT_PAGE_SIZE,
    pageSizeOptions = PAGE_SIZES,
    showSizeChanger = true,
  } = paginationConfig;

  const { defaultSortField, defaultSortOrder } = sortingConfig;

  // Create parsers for all table state features
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    const createdParsers = createTableParsers({
      pageSize: defaultPageSize,
    });
    return createdParsers;
  }, [defaultPageSize]);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state (URL is the single source of truth)
  const currentState: TableState<TSortField> = useMemo(() => {
    const state = {
      pageIndex: queryState.page ?? DEFAULT_PAGE_INDEX,
      pageSize: queryState.size ?? defaultPageSize,
      sortField: (queryState.sortField as TSortField) || defaultSortField, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      sortOrder:
        (queryState.sortOrder as SortOrder | undefined) || defaultSortOrder, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      columnFilters: queryState.filters ?? {},
      searchQuery: queryState.search || undefined, // Convert empty string to undefined
    };

    return state;
  }, [queryState, defaultPageSize, defaultSortField, defaultSortOrder]);

  // Update functions that update query state (URL is the single source of truth)
  const updatePagination = useCallback(
    (pageIndex: number, pageSize?: number) => {
      const newPageIndex =
        pageSize !== undefined && pageSize !== currentState.pageSize
          ? DEFAULT_PAGE_INDEX // Reset to first page when changing page size
          : pageIndex;

      const updates: QueryStateUpdates = { page: newPageIndex };
      if (pageSize !== undefined) {
        updates.size = pageSize;
      }
      setQueryState(updates);
    },
    [setQueryState, currentState.pageSize],
  );

  const updateSorting = useCallback(
    (sortField?: TSortField, sortOrder?: SortOrder) => {
      setQueryState({
        sortField: sortField ? String(sortField) : null,
        sortOrder: sortOrder ?? null,
        page: DEFAULT_PAGE_INDEX, // Reset to first page when sorting changes
      });
    },
    [setQueryState],
  );

  const updateFilters = useCallback(
    (filters: Record<string, FilterValue | null>) => {
      // Clean up filters by removing null/undefined values before syncing to URL
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value != null),
      );
      setQueryState({
        filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : null, // Use null to remove from URL when empty
        page: DEFAULT_PAGE_INDEX, // Reset to first page when filters change
      });
    },
    [setQueryState],
  );

  const updateSearch = useCallback(
    (searchQuery?: string) => {
      setQueryState({
        search: searchQuery || null,
        page: DEFAULT_PAGE_INDEX, // Reset to first page when search changes
      });
    },
    [setQueryState],
  );

  const resetState = useCallback(() => {
    // Reset all URL state
    const urlUpdates: QueryStateUpdates = {
      page: DEFAULT_PAGE_INDEX,
      size: defaultPageSize,
      sortField: null,
      sortOrder: null,
      filters: null,
      search: null,
    };

    setQueryState(urlUpdates);
  }, [setQueryState, defaultPageSize]);

  // Call onStateChange when state changes
  useEffect(() => {
    if (onStateChange) {
      onStateChange(currentState);
    }
  }, [currentState, onStateChange]);

  return {
    // Current state
    state: currentState,

    // Pagination
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

    // Configuration
    paginationConfig: {
      pageSizeOptions,
      showSizeChanger,
    },
  };
};
