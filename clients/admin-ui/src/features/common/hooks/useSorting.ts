import { parseAsString, parseAsStringLiteral, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import type {
  SortingConfig,
  SortingQueryParams,
  SortingState,
  SortOrder,
} from "./types";

/**
 * NuQS parsers for sorting state - synced to URL
 */
const createSortingParsers = () => ({
  sortField: parseAsString.withDefault(""),
  sortOrder: parseAsStringLiteral(["ascend", "descend"]),
});

/**
 * Custom hook for managing sorting state with URL synchronization
 *
 * This hook manages sorting state (sort field and sort order) and
 * synchronizes it with URL query parameters using NuQS. The URL query parameters
 * are the single source of truth for sorting state.
 *
 * Can be used standalone for any sortable component (not just tables) or
 * consumed by table state management hooks.
 *
 * @param config - Configuration for sorting state management
 * @returns Sorting state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const sorting = useSorting();
 *
 * // With custom default values
 * const sorting = useSorting({
 *   defaultSortField: 'name',
 *   defaultSortOrder: 'ascend'
 * });
 *
 * // With state change callback
 * const sorting = useSorting({
 *   onSortingChange: (state) => console.log('Sorting changed:', state)
 * });
 *
 * // Use with Ant Table component
 * <Table
 *   dataSource={data}
 *   columns={columns}
 *   onChange={(pagination, filters, sorter) => {
 *     if (!Array.isArray(sorter) && sorter) {
 *       sorting.updateSorting(
 *         sorter.field as string,
 *         sorter.order
 *       );
 *     }
 *   }}
 * />
 * ```
 */
export const useSorting = <TSortField extends string = string>(
  config: SortingConfig<TSortField> = {},
) => {
  const { defaultSortField, defaultSortOrder, onSortingChange } = config;

  // Create parsers for sorting state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => createSortingParsers(), []);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state (URL is the single source of truth)
  const currentState: SortingState<TSortField> = useMemo(
    () => ({
      sortField: (queryState.sortField as TSortField) || defaultSortField, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      sortOrder: (queryState.sortOrder as SortOrder | null) ?? defaultSortOrder, // Use `??` because parseAsStringLiteral returns null when not set
    }),
    [queryState, defaultSortField, defaultSortOrder],
  );

  // Update functions that update query state (URL is the single source of truth)
  const updateSorting = useCallback(
    (sortField?: TSortField, sortOrder?: SortOrder) => {
      const updates: SortingQueryParams = {
        sortField: sortField ? String(sortField) : null,
        sortOrder: sortOrder ?? null,
      };
      setQueryState(updates);
    },
    [setQueryState],
  );

  const resetSorting = useCallback(() => {
    // Reset sorting URL state
    setQueryState({
      sortField: null,
      sortOrder: null,
    });
  }, [setQueryState]);

  // Call onSortingChange when state changes
  useEffect(() => {
    if (onSortingChange) {
      onSortingChange(currentState);
    }
  }, [currentState, onSortingChange]);

  return {
    // Current state
    ...currentState,

    // Update functions
    updateSorting,
    resetSorting,

    // Ant Design table sorting props
    sortingProps: {
      sortDirections: ["ascend", "descend"] as const,
      defaultSortOrder: currentState.sortOrder,
      sortedInfo: currentState.sortField
        ? {
            field: currentState.sortField,
            order: currentState.sortOrder,
          }
        : undefined,
    },
  };
};
