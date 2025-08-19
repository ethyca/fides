import { useMemo } from "react";

import type { PaginationConfig } from "./types";
import { usePagination } from "./usePagination";

/**
 * Custom hook for Ant Design Pagination component integration
 *
 * This hook wraps the framework-agnostic usePagination hook and provides
 * Ant Design specific pagination props for the Pagination component.
 *
 * @param config - Configuration for pagination state management
 * @returns Pagination state, update functions, and Ant Design pagination props
 *
 * @example
 * ```tsx
 * // Basic usage with Ant Pagination component
 * const { paginationProps, pageIndex, pageSize } = useAntPagination();
 *
 * return (
 *   <Pagination
 *     {...paginationProps}
 *     total={totalItems}
 *     showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} items`}
 *   />
 * );
 *
 * // With custom configuration
 * const { paginationProps } = useAntPagination({
 *   defaultPageSize: 50,
 *   pageSizeOptions: [25, 50, 100, 200]
 * });
 * ```
 */
export const useAntPagination = (config: PaginationConfig = {}) => {
  const pagination = usePagination(config);

  const {
    pageIndex,
    pageSize,
    updatePageIndex,
    updatePageSize,
    pageSizeOptions,
    showSizeChanger,
  } = pagination;

  // Ant Design pagination props
  const paginationProps = useMemo(
    () => ({
      current: pageIndex,
      pageSize,
      showSizeChanger,
      pageSizeOptions: pageSizeOptions.map(String),
      onChange: updatePageIndex,
      onShowSizeChange: (_: number, newPageSize: number) => {
        updatePageSize(newPageSize);
      },
    }),
    [
      pageIndex,
      pageSize,
      showSizeChanger,
      pageSizeOptions,
      updatePageIndex,
      updatePageSize,
    ],
  );

  return {
    // Expose all pagination functionality
    ...pagination,

    // Ant Design specific props
    paginationProps,
  };
};
