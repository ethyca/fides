import { AntFilterValue as FilterValue } from "fidesui";
import { parseAsJson, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo, useState } from "react";

import { usePagination, useSearch, useSorting } from "../../hooks";
import type { SortOrder } from "../../sorting";
import type {
  QueryStateUpdates,
  TableState,
  TableStateConfig,
  TableStateWithHelpers,
} from "./types";

/**
 * NuQS parsers for filter state - synced to URL
 */
const createFilterParsers = () => {
  return {
    filters: parseAsJson(
      (value: unknown) => value as Record<string, FilterValue | null>,
    ).withDefault({}),
  };
};

/**
 * Custom hook for managing table state with optional URL synchronization
 *
 * This hook manages all table features (pagination, sorting, filtering, search) and
 * can optionally synchronize them with URL query parameters using NuQS. When URL sync
 * is disabled, it uses React state for in-memory state management.
 *
 * @param config - Configuration for table state management
 * @returns Table state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings (URL state enabled by default)
 * const tableState = useTableState();
 *
 * // With custom default values
 * const tableState = useTableState({
 *   pagination: { defaultPageSize: 50 },
 *   sorting: { defaultSortKey: 'name', defaultSortOrder: 'ascend' }
 * });
 *
 * // Without URL state synchronization
 * const tableState = useTableState({
 *   disableUrlState: true,
 *   pagination: { defaultPageSize: 50 },
 * });
 *
 * // Type-safe table state with enum constraints (recommended)
 * enum MyTableColumns {
 *   NAME = "name",
 *   TYPE = "type",
 *   CREATED_AT = "createdAt"
 * }
 *
 * const tableState = useTableState<MyTableColumns>({
 *   pagination: { defaultPageSize: 25 },
 *   sorting: {
 *     validColumns: Object.values(MyTableColumns), // Enforces URL validation
 *     defaultSortKey: MyTableColumns.NAME,
 *     defaultSortOrder: 'ascend'
 *   },
 *   onStateChange: (state) => console.log('Table state changed:', state)
 * });
 * // Now URL sorting is validated against the column enum
 * ```
 */
export const useTableState = <TSortKey extends string = string>(
  config: TableStateConfig<TSortKey> = {},
) => {
  const {
    pagination: paginationConfig = {},
    sorting: sortingConfig = {},
    search: searchConfig = {},
    onStateChange,
    disableUrlState = false,
  } = config;

  // Use the standalone pagination hook (with disableUrlState passed through)
  const {
    pageIndex,
    pageSize,
    resetPagination,
    updatePageIndex,
    updatePageSize,
    pageSizeOptions,
    showSizeChanger,
  } = usePagination({ ...paginationConfig, disableUrlState });

  // Use the standalone sorting hook (with disableUrlState passed through)
  const {
    sortKey,
    sortOrder,
    updateSorting: updateSortingOnly,
    resetSorting,
  } = useSorting<TSortKey>({ ...sortingConfig, disableUrlState });

  // Use the standalone search hook (with disableUrlState passed through)
  const {
    searchQuery,
    updateSearch: updateSearchOnly,
    resetSearch,
  } = useSearch({ ...searchConfig, disableUrlState });

  // React state for filter management (when disableUrlState is true)
  const [localFilters, setLocalFilters] = useState<
    Record<string, FilterValue | null>
  >({});

  // Create parsers for filter state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    if (disableUrlState) {
      return null;
    }
    return createFilterParsers();
  }, [disableUrlState]);

  // Use NuQS for URL state management (only when disableUrlState is false)
  const [queryState, setQueryState] = useQueryStates(parsers ?? {}, {
    history: "push",
  });

  // Create current state from either query state or local state
  const currentState: TableState<TSortKey> = useMemo(() => {
    const state = {
      pageIndex,
      pageSize,
      sortKey,
      sortOrder,
      columnFilters: disableUrlState
        ? localFilters
        : ((queryState as { filters?: Record<string, FilterValue | null> })
            .filters ?? {}),
      searchQuery,
    };

    return state;
  }, [
    disableUrlState,
    localFilters,
    queryState,
    pageIndex,
    pageSize,
    sortKey,
    sortOrder,
    searchQuery,
  ]);

  const updateSorting = useCallback(
    (sf?: TSortKey, so?: SortOrder) => {
      updateSortingOnly(sf, so);
      resetPagination();
    },
    [updateSortingOnly, resetPagination],
  );

  const updateFilters = useCallback(
    (filters: Record<string, FilterValue | null>) => {
      if (disableUrlState) {
        // Update local state
        setLocalFilters(filters);
      } else {
        // Clean up filters by removing null/undefined values before syncing to URL
        const cleanFilters = Object.fromEntries(
          Object.entries(filters).filter(([, value]) => value != null),
        );
        setQueryState({
          filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : null, // Use null to remove from URL when empty
        });
      }
      resetPagination();
    },
    [disableUrlState, setQueryState, resetPagination],
  );

  const updateSearch = useCallback(
    (searchString?: string) => {
      updateSearchOnly(searchString);
      resetPagination();
    },
    [updateSearchOnly, resetPagination],
  );

  const resetState = useCallback(() => {
    if (disableUrlState) {
      // Reset local state
      setLocalFilters({});
    } else {
      // Reset all URL state
      const urlUpdates: QueryStateUpdates = {
        filters: null,
      };
      setQueryState(urlUpdates);
    }
    resetPagination();
    resetSorting();
    resetSearch();
  }, [
    disableUrlState,
    setQueryState,
    resetPagination,
    resetSorting,
    resetSearch,
  ]);

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
    updatePageIndex,
    updatePageSize,

    // Sorting (delegated to sorting hook)
    sortKey: currentState.sortKey,
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
  } as TableStateWithHelpers<TSortKey>;
};
