import { AntFilterValue as FilterValue } from "fidesui";
import { parseAsJson, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import { usePagination, useSearch, useSorting } from "../../hooks";
import { useLocalStorage } from "../../hooks/useLocalStorage";
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
 * Custom hook for managing table state with URL synchronization and localStorage persistence
 *
 * This hook manages all table features (pagination, sorting, filtering, search) and
 * synchronizes them with URL query parameters using NuQS. Column widths are stored
 * in localStorage as user preferences. The URL query parameters are the single source
 * of truth for table state, while localStorage handles user UI preferences.
 *
 * Features:
 * - Pagination, sorting, filtering, search synced to URL
 * - Column widths persisted to localStorage (per tableId)
 * - Type-safe column constraints with TypeScript enums
 * - Automatic reset functionality for all state
 *
 * @param config - Configuration for table state management
 * @returns Table state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const tableState = useTableState({ tableId: "my-table" });
 *
 * // With custom default values
 * const tableState = useTableState({
 *   tableId: "my-table",
 *   pagination: { defaultPageSize: 50 },
 *   sorting: { defaultSortKey: 'name', defaultSortOrder: 'ascend' }
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
 *   tableId: "my-table",
 *   pagination: { defaultPageSize: 25 },
 *   sorting: {
 *     validColumns: Object.values(MyTableColumns), // Enforces URL validation
 *     defaultSortKey: MyTableColumns.NAME,
 *     defaultSortOrder: 'ascend'
 *   },
 *   onStateChange: (state) => console.log('Table state changed:', state)
 * });
 *
 * // Using with CustomTable for column resizing
 * const columns = [
 *   {
 *     title: 'Name',
 *     dataIndex: 'name',
 *     key: 'name',
 *     width: tableState.columnWidths?.name || 150, // Use stored width or default
 *   },
 *   // ... other columns
 * ];
 *
 * // The CustomTable component will call tableState.updateColumnWidth
 * // when columns are resized, automatically persisting to localStorage
 * ```
 */
export const useTableState = <TSortKey extends string = string>(
  config: TableStateConfig<TSortKey>,
) => {
  const {
    tableId,
    pagination: paginationConfig = {},
    sorting: sortingConfig = {},
    search: searchConfig = {},
    onStateChange,
  } = config;

  // Use local storage for column widths (user preference, not URL state)
  const [columnWidths, setColumnWidths] = useLocalStorage<
    Record<string, number>
  >(`${tableId}:column-widths`, {});

  // Use the standalone pagination hook
  const {
    pageIndex,
    pageSize,
    resetPagination,
    updatePageIndex,
    updatePageSize,
    pageSizeOptions,
    showSizeChanger,
  } = usePagination(paginationConfig);

  // Use the standalone sorting hook
  const {
    sortKey,
    sortOrder,
    updateSorting: updateSortingOnly,
    resetSorting,
  } = useSorting<TSortKey>(sortingConfig);

  // Use the standalone search hook
  const {
    searchQuery,
    updateSearch: updateSearchOnly,
    resetSearch,
  } = useSearch(searchConfig);

  // Create parsers for filter state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => createFilterParsers(), []);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state, pagination hook, sorting hook, search hook, and local storage
  const currentState: TableState<TSortKey> = useMemo(() => {
    const state = {
      pageIndex,
      pageSize,
      sortKey,
      sortOrder,
      columnFilters: queryState.filters ?? {},
      searchQuery,
      columnWidths,
    };

    return state;
  }, [
    queryState,
    pageIndex,
    pageSize,
    sortKey,
    sortOrder,
    searchQuery,
    columnWidths,
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
      // Clean up filters by removing null/undefined values before syncing to URL
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value != null),
      );
      setQueryState({
        filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : null, // Use null to remove from URL when empty
      });
      resetPagination();
    },
    [setQueryState, resetPagination],
  );

  const updateSearch = useCallback(
    (searchString?: string) => {
      updateSearchOnly(searchString);
      resetPagination();
    },
    [updateSearchOnly, resetPagination],
  );

  const updateColumnWidth = useCallback(
    (columnKey: string, width: number) => {
      const updatedWidths = {
        ...columnWidths,
        [columnKey]: width,
      };
      setColumnWidths(updatedWidths);
    },
    [columnWidths, setColumnWidths],
  );

  const resetColumnWidths = useCallback(() => {
    setColumnWidths({});
  }, [setColumnWidths]);

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

    // Column widths (stored in localStorage)
    columnWidths: currentState.columnWidths,
    updateColumnWidth,
    resetColumnWidths,

    // Reset
    resetState,

    // Configuration (delegated to pagination hook)
    paginationConfig: {
      pageSizeOptions,
      showSizeChanger,
    },
  } as TableStateWithHelpers<TSortKey>;
};
