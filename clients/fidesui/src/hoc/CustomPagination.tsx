import { PaginationProps } from "antd/es/pagination";
import { Pagination } from "antd/lib";
import React from "react";

// Exportable constant for consistent page size options across the app
export const PAGE_SIZES = [25, 50, 100];

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Pagination component.
 *
 * Default customizations:
 * - Enables showSizeChanger for user-controlled page size selection
 * - Uses consistent PAGE_SIZES options
 *
 */
export const CustomPagination = ({
  showSizeChanger = true,
  pageSizeOptions = PAGE_SIZES.map(String),
  ...props
}: PaginationProps) => {
  return (
    <Pagination
      showSizeChanger={showSizeChanger}
      pageSizeOptions={pageSizeOptions}
      {...props}
    />
  );
};
