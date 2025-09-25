import { parseAsNumberLiteral, useQueryStates } from "nuqs";
import { useMemo, useState } from "react";

import { parseAsPositiveInteger } from "../hooks/nuqs-parsers";
import type { PaginationConfig, PaginationState } from "../pagination";
import {
  DEFAULT_PAGE_INDEX,
  DEFAULT_PAGE_SIZE,
  DEFAULT_PAGE_SIZES,
} from "../table/constants";

/**
 * NuQS parsers for pagination state - synced to URL
 */
const createPaginationParsers = (
  defaults: {
    pageSize?: number;
    pageSizeOptions?: readonly number[];
    pageQueryKey?: string;
    sizeQueryKey?: string;
  } = {},
) => {
  const pageKey = defaults.pageQueryKey || "page";
  const sizeKey = defaults.sizeQueryKey || "size";

  return {
    [pageKey]: parseAsPositiveInteger.withDefault(DEFAULT_PAGE_INDEX),
    [sizeKey]: defaults.pageSizeOptions
      ? parseAsNumberLiteral(defaults.pageSizeOptions).withDefault(
          defaults.pageSize ?? DEFAULT_PAGE_SIZE,
        )
      : parseAsPositiveInteger.withDefault(
          defaults.pageSize ?? DEFAULT_PAGE_SIZE,
        ),
  };
};

/**
 * Custom hook for managing pagination state with optional URL synchronization
 *
 * This hook manages pagination state (current page and page size) and can optionally
 * synchronize it with URL query parameters using NuQS. When URL sync is disabled,
 * it uses React state for in-memory state management.
 *
 * This hook is framework agnostic and provides core pagination logic. For Ant Design
 * specific integration, use `useAntPagination` which wraps this hook.
 *
 * @param config - Configuration for pagination state management
 * @returns Pagination state and update functions
 *
 * @example
 * ```tsx
 * // Basic usage with default settings (URL state enabled by default)
 * const pagination = usePagination();
 *
 * // With custom default values
 * const pagination = usePagination({
 *   defaultPageSize: 50,
 *   pageSizeOptions: [25, 50, 100, 200]
 * });
 *
 * // Without URL state synchronization
 * const pagination = usePagination({
 *   disableUrlState: true,
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
    pageQueryKey = "page",
    sizeQueryKey = "size",
    disableUrlState = false,
  } = config;

  // Use defaults for UI/display purposes, but keep original value for parser logic
  const displayPageSizeOptions = pageSizeOptions ?? DEFAULT_PAGE_SIZES;

  // React state for in-memory state management (when disableUrlState is true)
  const [localState, setLocalState] = useState<PaginationState>({
    pageIndex: DEFAULT_PAGE_INDEX,
    pageSize: defaultPageSize,
  });

  // Create parsers for pagination state
  // Note: Parsers must be stable across renders for NuQS to work properly
  const parsers = useMemo(() => {
    if (disableUrlState) {
      return null;
    }
    return createPaginationParsers({
      pageSize: defaultPageSize,
      pageSizeOptions, // Pass undefined if user didn't provide it
      pageQueryKey,
      sizeQueryKey,
    });
  }, [
    defaultPageSize,
    pageSizeOptions,
    pageQueryKey,
    sizeQueryKey,
    disableUrlState,
  ]);

  // Use NuQS for URL state management (only when disableUrlState is false)
  const [queryState, setQueryState] = useQueryStates(parsers ?? {}, {
    history: "push",
  });

  // Create current state from either query state or local state
  const currentState: PaginationState = disableUrlState
    ? localState
    : {
        pageIndex: queryState[pageQueryKey] ?? DEFAULT_PAGE_INDEX,
        pageSize: queryState[sizeQueryKey] ?? defaultPageSize,
      };

  const updatePageIndex = (pageIndex: number) => {
    if (disableUrlState) {
      setLocalState((prev) => ({ ...prev, pageIndex }));
    } else {
      setQueryState({ [pageQueryKey]: pageIndex });
    }
  };

  const nextPage = () => {
    if (disableUrlState) {
      setLocalState((prev) => ({
        ...prev,
        pageIndex: prev.pageIndex + 1,
      }));
    } else {
      setQueryState((prevState) => {
        return prevState
          ? {
              [pageQueryKey]:
                (prevState[pageQueryKey] ?? DEFAULT_PAGE_INDEX) + 1,
              [sizeQueryKey]: prevState[sizeQueryKey],
            }
          : {};
      });
    }
  };

  const previousPage = () => {
    if (disableUrlState) {
      setLocalState((prev) => ({
        ...prev,
        pageIndex: prev.pageIndex - 1,
      }));
    } else {
      setQueryState((prevState) => {
        return {
          [pageQueryKey]: (prevState[pageQueryKey] ?? DEFAULT_PAGE_INDEX) - 1,
          [sizeQueryKey]: prevState[sizeQueryKey],
        };
      });
    }
  };

  const updatePageSize = (pageSize: number) => {
    if (disableUrlState) {
      setLocalState({
        pageIndex:
          pageSize !== currentState.pageSize
            ? DEFAULT_PAGE_INDEX
            : currentState.pageIndex,
        pageSize,
      });
    } else {
      setQueryState({
        [pageQueryKey]:
          pageSize !== currentState.pageSize
            ? DEFAULT_PAGE_INDEX
            : currentState.pageIndex,
        [sizeQueryKey]: pageSize,
      });
    }
  };

  const resetPagination = () => {
    if (disableUrlState) {
      // Reset local state
      setLocalState({
        pageIndex: DEFAULT_PAGE_INDEX,
        pageSize: defaultPageSize,
      });
    } else {
      // Reset pagination URL state
      setQueryState({
        [pageQueryKey]: DEFAULT_PAGE_INDEX,
        [sizeQueryKey]: defaultPageSize,
      });
    }
  };

  return {
    // Current state
    ...currentState,

    // Update functions
    updatePageIndex,
    updatePageSize,
    resetPagination,
    nextPage,
    previousPage,

    // Configuration for components
    pageSizeOptions: displayPageSizeOptions,
    showSizeChanger,
  };
};
