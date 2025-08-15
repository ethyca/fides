import { parseAsString, useQueryStates } from "nuqs";
import { useCallback, useEffect, useMemo } from "react";

import type {
  SearchConfig,
  SearchQueryParams,
  SearchState,
} from "./types";

/**
 * NuQS parsers for search state - synced to URL
 */
const createSearchParsers = () => ({
  search: parseAsString.withDefault(""),
});

/**
 * Custom hook for managing search state with URL synchronization
 *
 * This hook manages search state (search query) and
 * synchronizes it with URL query parameters using NuQS. The URL query parameters
 * are the single source of truth for search state.
 *
 * Can be used standalone for any searchable component (not just tables) or
 * consumed by table state management hooks.
 *
 * @param config - Configuration for search state management
 * @returns Search state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const search = useSearch();
 *
 * // With custom default value
 * const search = useSearch({
 *   defaultSearchQuery: 'initial query'
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
  const { defaultSearchQuery, onSearchChange } = config;

  // Create parsers for search state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => createSearchParsers(), []);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state (URL is the single source of truth)
  const currentState: SearchState = useMemo(
    () => ({
      searchQuery: queryState.search || defaultSearchQuery || undefined, // Convert empty string to undefined, fallback to default
    }),
    [queryState, defaultSearchQuery],
  );

  // Update functions that update query state (URL is the single source of truth)
  const updateSearch = useCallback(
    (searchQuery?: string) => {
      const updates: SearchQueryParams = {
        search: searchQuery || null, // Use null to remove from URL when empty
      };
      setQueryState(updates);
    },
    [setQueryState],
  );

  const resetSearch = useCallback(() => {
    // Reset search URL state
    setQueryState({
      search: null,
    });
  }, [setQueryState]);

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
