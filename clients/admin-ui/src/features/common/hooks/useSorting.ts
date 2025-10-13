import {
  parseAsString,
  parseAsStringEnum,
  parseAsStringLiteral,
  useQueryStates,
} from "nuqs";
import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  SortingConfig,
  SortingQueryParams,
  SortingState,
  SortOrder,
} from "../sorting";

/**
 * NuQS parsers for sorting state - synced to URL
 */
const createSortingParsers = <TSortKey extends string = string>(
  validColumns?: readonly TSortKey[],
) => ({
  sortKey: validColumns
    ? parseAsStringEnum<TSortKey>([...validColumns])
    : parseAsString.withDefault(""),
  sortOrder: parseAsStringLiteral(["ascend", "descend"]),
});

/**
 * Custom hook for managing sorting state with optional URL synchronization
 *
 * This hook manages sorting state (sort field and sort order) and can optionally
 * synchronize it with URL query parameters using NuQS. When URL sync is disabled,
 * it uses React state for in-memory state management.
 *
 * Can be used standalone for any sortable component (not just tables) or
 * consumed by table state management hooks.
 *
 * @param config - Configuration for sorting state management
 * @returns Sorting state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings (URL state enabled by default)
 * const sorting = useSorting();
 *
 * // With custom default values
 * const sorting = useSorting({
 *   defaultSortKey: 'name',
 *   defaultSortOrder: 'ascend'
 * });
 *
 * // Without URL state synchronization
 * const sorting = useSorting({
 *   disableUrlState: true,
 * });
 *
 * // With state change callback
 * const sorting = useSorting({
 *   onSortingChange: (state) => console.log('Sorting changed:', state)
 * });
 *
 * // Type-safe sorting with enum constraints
 * enum MyColumnKeys {
 *   NAME = "name",
 *   TYPE = "type",
 *   CREATED_AT = "createdAt"
 * }
 *
 * const sorting = useSorting<MyColumnKeys>({
 *   validColumns: Object.values(MyColumnKeys),
 *   defaultSortKey: MyColumnKeys.NAME,
 *   defaultSortOrder: 'ascend'
 * });
 * // Only valid column keys are accepted from URL params
 * // Invalid sortKey values in URL will have no effect
 *
 * // Use with Ant Table component
 * <Table
 *   dataSource={data}
 *   columns={columns}
 *   onChange={(pagination, filters, sorter) => {
 *     if (!Array.isArray(sorter) && sorter) {
 *       sorting.updateSorting(
 *         sorter.field as MyColumnKeys,
 *         sorter.order
 *       );
 *     }
 *   }}
 * />
 * ```
 */
export const useSorting = <TSortKey extends string = string>(
  config: SortingConfig<TSortKey> = {},
) => {
  const {
    defaultSortKey,
    defaultSortOrder,
    onSortingChange,
    validColumns,
    disableUrlState = false,
  } = config;

  // React state for in-memory state management (when disableUrlState is true)
  const [localState, setLocalState] = useState<SortingState<TSortKey>>({
    sortKey: defaultSortKey,
    sortOrder: defaultSortOrder,
  });

  // Create parsers for sorting state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    if (disableUrlState) {
      return null;
    }
    return createSortingParsers(validColumns);
  }, [disableUrlState, validColumns]);

  // Use NuQS for URL state management (only when disableUrlState is false)
  const [queryState, setQueryState] = useQueryStates(parsers ?? {}, {
    history: "push",
  });

  // Create current state from either query state or local state
  const currentState: SortingState<TSortKey> = useMemo(() => {
    if (disableUrlState) {
      return localState;
    }
    return {
      sortKey:
        ((queryState as { sortKey?: string }).sortKey as TSortKey) ||
        defaultSortKey, // Use `||` not `??` because NuQS defaults to empty string, not null/undefined
      sortOrder:
        ((queryState as { sortOrder?: SortOrder })
          .sortOrder as SortOrder | null) ?? defaultSortOrder, // Use `??` because parseAsStringLiteral returns null when not set
    };
  }, [
    disableUrlState,
    localState,
    queryState,
    defaultSortKey,
    defaultSortOrder,
  ]);

  // Update functions that update either query state or local state
  const updateSorting = useCallback(
    (sortKey?: TSortKey, sortOrder?: SortOrder) => {
      if (disableUrlState) {
        setLocalState({ sortKey, sortOrder });
      } else {
        const updates: SortingQueryParams = {
          sortKey: sortKey ? String(sortKey) : null,
          sortOrder: sortOrder ?? null,
        };
        setQueryState(updates);
      }
    },
    [disableUrlState, setQueryState],
  );

  const resetSorting = useCallback(() => {
    if (disableUrlState) {
      // Reset local state
      setLocalState({
        sortKey: defaultSortKey,
        sortOrder: defaultSortOrder,
      });
    } else {
      // Reset sorting URL state
      setQueryState({
        sortKey: null,
        sortOrder: null,
      });
    }
  }, [disableUrlState, defaultSortKey, defaultSortOrder, setQueryState]);

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
      sortedInfo: currentState.sortKey
        ? {
            field: currentState.sortKey,
            order: currentState.sortOrder,
          }
        : undefined,
    },
  };
};
