import { PAGE_SIZES } from "fidesui";
import {
  parseAsInteger,
  parseAsJson,
  parseAsString,
  useQueryStates,
} from "nuqs";
import { useCallback, useEffect, useMemo, useState } from "react";

import { TableState, TableStateConfig, TableUrlSyncConfig } from "./types";

/**
 * Default configuration values
 */
const DEFAULT_PAGE_SIZE = PAGE_SIZES[0];
const DEFAULT_PAGE_INDEX = 1;
const DEFAULT_URL_SYNC: TableUrlSyncConfig = {
  pagination: true,
  sorting: true,
  filtering: true,
  search: true,
};

/**
 * NuQS parsers for table state - only for features that should sync to URL
 */
const createTableParsers = (
  urlSync: TableUrlSyncConfig,
  defaults: {
    pageSize?: number;
  } = {},
) => ({
  ...(urlSync.pagination && {
    page: parseAsInteger.withDefault(DEFAULT_PAGE_INDEX),
    size: parseAsInteger.withDefault(defaults.pageSize ?? DEFAULT_PAGE_SIZE),
  }),
  ...(urlSync.sorting && {
    sortField: parseAsString.withDefault(""),
    sortOrder: parseAsString.withDefault(""),
  }),
  ...(urlSync.filtering && {
    filters: parseAsJson((value: any) => value).withDefault({}),
  }),
  ...(urlSync.search && {
    search: parseAsString.withDefault(""),
  }),
});

/**
 * Custom hook for managing table state with optional URL synchronization
 *
 * This hook maintains internal state for all table features (pagination, sorting, filtering, search)
 * and optionally syncs specific features to the URL based on the urlSync configuration.
 *
 * When urlSync is disabled for a feature, that feature still works but is only managed internally
 * without affecting the URL. This ensures all table functionality remains available regardless
 * of URL sync settings.
 *
 * @param config - Configuration for table state management
 * @returns Table state and update functions
 *
 * @example
 * ```tsx
 * // All features synced to URL (default behavior)
 * const tableState = useTableState({
 *   pagination: { defaultPageSize: 50 },
 *   sorting: { defaultSortField: 'name', defaultSortOrder: 'ascend' }
 * });
 *
 * // Explicitly enable all URL sync features
 * const tableState = useTableState({
 *   urlSync: { pagination: true, sorting: true, filtering: true, search: true }
 * });
 *
 * // Only pagination synced to URL, other features work internally
 * const tableState = useTableState({
 *   urlSync: { pagination: true, sorting: false, filtering: false, search: false }
 * });
 *
 * // Disable all URL sync, everything works internally
 * const tableState = useTableState({
 *   urlSync: { pagination: false, sorting: false, filtering: false, search: false }
 * });
 * ```
 */
export const useTableState = (config: TableStateConfig = {}) => {
  const {
    urlSync: urlSyncConfig = {},
    pagination: paginationConfig = {},
    sorting: sortingConfig = {},
    onStateChange,
  } = config;

  // Merge urlSync config with defaults, preserving explicit false values
  const urlSync = useMemo(
    () => ({
      pagination: urlSyncConfig.pagination ?? DEFAULT_URL_SYNC.pagination,
      sorting: urlSyncConfig.sorting ?? DEFAULT_URL_SYNC.sorting,
      filtering: urlSyncConfig.filtering ?? DEFAULT_URL_SYNC.filtering,
      search: urlSyncConfig.search ?? DEFAULT_URL_SYNC.search,
    }),
    [urlSyncConfig],
  );

  const {
    defaultPageSize = DEFAULT_PAGE_SIZE,
    pageSizeOptions = PAGE_SIZES,
    showSizeChanger = true,
  } = paginationConfig;

  const { defaultSortField, defaultSortOrder } = sortingConfig;

  // Internal state for features not synced to URL
  const [internalState, setInternalState] = useState({
    pageIndex: DEFAULT_PAGE_INDEX,
    pageSize: defaultPageSize,
    sortField: defaultSortField,
    sortOrder: defaultSortOrder,
    columnFilters: {},
    searchQuery: undefined as string | undefined,
  });

  // Create parsers only for features that should sync to URL
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    const createdParsers = createTableParsers(urlSync, {
      pageSize: defaultPageSize,
    });
    return createdParsers;
  }, [urlSync, defaultPageSize]);

  // Use NuQS for URL state management (only for enabled features)
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
    shallow: false,
  });

  // Merge URL state with internal state, prioritizing URL when available
  const currentState: TableState = useMemo(() => {
    const state = {
      pageIndex: urlSync.pagination
        ? (queryState.page ?? DEFAULT_PAGE_INDEX)
        : internalState.pageIndex,
      pageSize: urlSync.pagination
        ? (queryState.size ?? defaultPageSize)
        : internalState.pageSize,
      sortField: urlSync.sorting
        ? queryState.sortField || defaultSortField // Use || not ?? because NuQS defaults to empty string, not null/undefined
        : internalState.sortField,
      sortOrder: urlSync.sorting
        ? (queryState.sortOrder as "ascend" | "descend" | undefined) ||
          defaultSortOrder // Use || not ?? because NuQS defaults to empty string, not null/undefined
        : internalState.sortOrder,
      columnFilters: urlSync.filtering
        ? (queryState.filters ?? {})
        : internalState.columnFilters,
      searchQuery: urlSync.search
        ? queryState.search
        : internalState.searchQuery,
      selectedRowKeys: [], // Selection is not synced to URL by default
    };

    return state;
  }, [
    queryState,
    internalState,
    urlSync,
    defaultPageSize,
    defaultSortField,
    defaultSortOrder,
  ]);

  // Update functions that handle both URL sync and internal state
  const updatePagination = useCallback(
    (pageIndex: number, pageSize?: number) => {
      const newPageIndex =
        pageSize !== undefined && pageSize !== currentState.pageSize
          ? DEFAULT_PAGE_INDEX // Reset to first page when changing page size
          : pageIndex;

      if (urlSync.pagination) {
        const updates: any = { page: newPageIndex };
        if (pageSize !== undefined) {
          updates.size = pageSize;
        }
        setQueryState(updates);
      } else {
        setInternalState((prev) => ({
          ...prev,
          pageIndex: newPageIndex,
          ...(pageSize !== undefined && { pageSize }),
        }));
      }
    },
    [
      setQueryState,
      setInternalState,
      currentState.pageSize,
      urlSync.pagination,
    ],
  );

  const updateSorting = useCallback(
    (sortField?: string, sortOrder?: "ascend" | "descend") => {
      if (urlSync.sorting) {
        setQueryState({
          sortField: sortField ?? null,
          sortOrder: sortOrder ?? null,
          ...(urlSync.pagination && { page: DEFAULT_PAGE_INDEX }), // Reset to first page when sorting changes, if pagination is URL synced. TODO: if we clear page when it's set to 1, this may not be needed.
        });
      } else {
        setInternalState((prev) => ({
          ...prev,
          sortField,
          sortOrder,
          pageIndex: DEFAULT_PAGE_INDEX, // Always reset to first page when sorting changes
        }));
      }
    },
    [setQueryState, setInternalState, urlSync.sorting, urlSync.pagination],
  );

  const updateFilters = useCallback(
    (filters: Record<string, any>) => {
      if (urlSync.filtering) {
        // Clean up filters by removing null/undefined values before syncing to URL
        const cleanFilters = Object.fromEntries(
          Object.entries(filters).filter(([, value]) => value != null),
        );
        setQueryState({
          filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : null, // Use null to remove from URL when empty
          ...(urlSync.pagination && { page: DEFAULT_PAGE_INDEX }), // Reset to first page when filters change, if pagination is URL synced
        });
      } else {
        setInternalState((prev) => ({
          ...prev,
          columnFilters: filters,
          pageIndex: DEFAULT_PAGE_INDEX, // Always reset to first page when filters change
        }));
      }
    },
    [setQueryState, setInternalState, urlSync.filtering, urlSync.pagination],
  );

  const updateSearch = useCallback(
    (searchQuery?: string) => {
      if (urlSync.search) {
        setQueryState({
          search: searchQuery || null,
          ...(urlSync.pagination && { page: DEFAULT_PAGE_INDEX }), // Reset to first page when search changes, if pagination is URL synced
        });
      } else {
        setInternalState((prev) => ({
          ...prev,
          searchQuery,
          pageIndex: DEFAULT_PAGE_INDEX, // Always reset to first page when search changes
        }));
      }
    },
    [setQueryState, setInternalState, urlSync.search, urlSync.pagination],
  );

  const resetState = useCallback(() => {
    // Reset URL state for synced features
    const urlUpdates: any = {};
    if (urlSync.pagination) {
      urlUpdates.page = DEFAULT_PAGE_INDEX;
      urlUpdates.size = defaultPageSize;
    }
    if (urlSync.sorting) {
      urlUpdates.sortField = null;
      urlUpdates.sortOrder = null;
    }
    if (urlSync.filtering) {
      urlUpdates.filters = null;
    }
    if (urlSync.search) {
      urlUpdates.search = null;
    }

    if (Object.keys(urlUpdates).length > 0) {
      setQueryState(urlUpdates);
    }

    // Reset internal state
    setInternalState({
      pageIndex: DEFAULT_PAGE_INDEX,
      pageSize: defaultPageSize,
      sortField: defaultSortField,
      sortOrder: defaultSortOrder,
      columnFilters: {},
      searchQuery: undefined,
    });
  }, [
    setQueryState,
    setInternalState,
    defaultPageSize,
    defaultSortField,
    defaultSortOrder,
    urlSync,
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
