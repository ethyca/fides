import { parseAsString, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { SearchConfig, SearchQueryParams, SearchState } from "../search";

/**
 * NuQS parsers for search state - synced to URL
 */
const createSearchParsers = () => ({
  search: parseAsString.withDefault(""),
});

/**
 * Custom hook for managing search state with optional URL synchronization
 *
 * This hook manages search state (search query) and can optionally
 * synchronize it with URL query parameters using NuQS. When URL sync is disabled,
 * it uses React state for in-memory state management.
 *
 * Can be used standalone for any searchable component (not just tables) or
 * consumed by table state management hooks.
 *
 * @param config - Configuration for search state management
 * @returns Search state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings (URL state enabled by default)
 * const search = useSearch();
 *
 * // With custom default value
 * const search = useSearch({
 *   defaultSearchQuery: 'initial query'
 * });
 *
 * // Without URL state synchronization
 * const search = useSearch({
 *   disableUrlState: true,
 * });
 *
 * // With state change callback
 * const search = useSearch({
 *   onSearchChange: (state) => console.log('Search changed:', state)
 * });
 *
 * // Use with DebouncedSearchInput component
 * <DebouncedSearchInput
 *   value={search.searchQuery}
 *   onChange={search.updateSearch}
 *   placeholder="Search..."
 * />
 * ```
 */
export const useSearch = (config: SearchConfig = {}) => {
  const {
    defaultSearchQuery,
    onSearchChange,
    disableUrlState = false,
  } = config;

  // React state for in-memory state management (when disableUrlState is true)
  const [localState, setLocalState] = useState<SearchState>({
    searchQuery: defaultSearchQuery || undefined,
  });

  // Create parsers for search state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    if (disableUrlState) {
      return null;
    }
    return createSearchParsers();
  }, [disableUrlState]);

  // Use NuQS for URL state management (only when disableUrlState is false)
  const [queryState, setQueryState] = useQueryStates(parsers ?? {}, {
    history: "push",
  });

  // Create current state from either query state or local state
  const currentState: SearchState = useMemo(() => {
    if (disableUrlState) {
      return localState;
    }
    return {
      searchQuery:
        (queryState as { search?: string }).search ||
        defaultSearchQuery ||
        undefined, // Convert empty string to undefined, fallback to default
    };
  }, [disableUrlState, localState, queryState, defaultSearchQuery]);

  // Update functions that update either query state or local state
  const updateSearch = useCallback(
    (searchQuery?: string) => {
      if (disableUrlState) {
        setLocalState({ searchQuery: searchQuery || undefined });
      } else {
        const updates: SearchQueryParams = {
          search: searchQuery || null, // Use null to remove from URL when empty
        };
        setQueryState(updates);
      }
    },
    [disableUrlState, setQueryState],
  );

  const resetSearch = useCallback(() => {
    if (disableUrlState) {
      // Reset local state
      setLocalState({ searchQuery: defaultSearchQuery || undefined });
    } else {
      // Reset search URL state
      setQueryState({
        search: null,
      });
    }
  }, [disableUrlState, defaultSearchQuery, setQueryState]);

  // Call onSearchChange when state changes
  useEffect(() => {
    if (onSearchChange) {
      onSearchChange(currentState);
    }
  }, [currentState, onSearchChange]);

  return {
    // Current state
    ...currentState,

    // Update functions
    updateSearch,
    resetSearch,

    // Convenience helper for search input components
    searchProps: {
      value: currentState.searchQuery || "",
      onChange: updateSearch,
      onClear: () => updateSearch(""),
    },
  };
};
