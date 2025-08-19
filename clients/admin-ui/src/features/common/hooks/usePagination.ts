import { parseAsNumberLiteral, useQueryStates } from "nuqs";
import { useMemo } from "react";

import {
  DEFAULT_PAGE_INDEX,
  DEFAULT_PAGE_SIZE,
  DEFAULT_PAGE_SIZES,
} from "../table/constants";
import { parseAsPositiveInteger } from "./nuqs-parsers";
import type { PaginationConfig, PaginationState } from "./types";

/**
 * NuQS parsers for pagination state - synced to URL
 */
const createPaginationParsers = (
  defaults: { pageSize?: number; pageSizeOptions?: readonly number[] } = {},
) => ({
  page: parseAsPositiveInteger.withDefault(DEFAULT_PAGE_INDEX),
  size: defaults.pageSizeOptions
    ? parseAsNumberLiteral(defaults.pageSizeOptions).withDefault(
        defaults.pageSize ?? DEFAULT_PAGE_SIZE,
      )
    : parseAsPositiveInteger.withDefault(
        defaults.pageSize ?? DEFAULT_PAGE_SIZE,
      ),
});

/**
 * Custom hook for managing pagination state with URL synchronization
 *
 * This hook manages pagination state (current page and page size) and
 * synchronizes it with URL query parameters using NuQS. The URL query parameters
 * are the single source of truth for pagination state.
 *
 * This hook is framework agnostic and provides core pagination logic. For Ant Design
 * specific integration, use `useAntPagination` which wraps this hook.
 *
 * @param config - Configuration for pagination state management
 * @returns Pagination state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings
 * const pagination = usePagination();
 *
 * // With custom default values
 * const pagination = usePagination({
 *   defaultPageSize: 50,
 *   pageSizeOptions: [25, 50, 100, 200]
 * });
 *
 * // Access state and update functions
 * const { pageIndex, pageSize, updatePageIndex, updatePageSize } = pagination;
 * ```
 */
export const usePagination = (config: PaginationConfig = {}) => {
  const {
    defaultPageSize = DEFAULT_PAGE_SIZE,
    pageSizeOptions,
    showSizeChanger = true,
  } = config;

  // Use defaults for UI/display purposes, but keep original value for parser logic
  const displayPageSizeOptions = pageSizeOptions ?? DEFAULT_PAGE_SIZES;

  // Create parsers for pagination state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    const createdParsers = createPaginationParsers({
      pageSize: defaultPageSize,
      pageSizeOptions, // Pass undefined if user didn't provide it
    });
    return createdParsers;
  }, [defaultPageSize, pageSizeOptions]);

  // Use NuQS for URL state management
  const [queryState, setQueryState] = useQueryStates(parsers, {
    history: "push",
  });

  // Create current state from query state (URL is the single source of truth)
  const currentState: PaginationState = {
    pageIndex: queryState.page ?? DEFAULT_PAGE_INDEX,
    pageSize: queryState.size ?? defaultPageSize,
  };

  const updatePageIndex = (pageIndex: number) => {
    setQueryState({ page: pageIndex });
  };

  const updatePageSize = (pageSize: number) => {
    setQueryState({
      page:
        pageSize !== currentState.pageSize
          ? DEFAULT_PAGE_INDEX
          : currentState.pageIndex,
      size: pageSize,
    });
  };

  const resetPagination = () => {
    // Reset pagination URL state
    setQueryState({
      page: DEFAULT_PAGE_INDEX,
      size: defaultPageSize,
    });
  };

  return {
    // Current state
    ...currentState,

    // Update functions
    updatePageIndex,
    updatePageSize,
    resetPagination,

    // Configuration for components
    pageSizeOptions: displayPageSizeOptions,
    showSizeChanger,
  };
};
