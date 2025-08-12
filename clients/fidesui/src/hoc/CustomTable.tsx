import { TableProps } from "antd/es/table";
import { Table } from "antd/lib";
import React from "react";

import { PAGE_SIZES } from "./CustomPagination";

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Table component.
 *
 * Default customizations:
 * - Uses "small" size for more compact rows
 * - Enables bordered styling for better visual separation
 * - Automatically hides pagination when there's only one page
 * - Uses CustomPagination defaults (showSizeChanger=true, consistent PAGE_SIZES)
 *
 */
export const CustomTable = <RecordType = any,>({
  size = "small",
  bordered = true,
  pagination,
  dataSource,
  scroll = { scrollToFirstRowOnChange: true, x: "max-content" },
  ...props
}: TableProps<RecordType>) => {
  const paginationDefaults = React.useMemo(() => {
    if (pagination === false || !pagination) {
      return pagination;
    }

    return {
      // Apply CustomPagination defaults first
      showSizeChanger: true,
      pageSizeOptions: PAGE_SIZES.map(String),
      hideOnSinglePage: true,
      // Then apply any user-provided config (allows overriding defaults)
      ...pagination,
    };
  }, [pagination, dataSource]);

  return (
    <Table
      size={size}
      bordered={bordered}
      pagination={paginationDefaults}
      dataSource={dataSource}
      scroll={scroll}
      {...props}
    />
  );
};
