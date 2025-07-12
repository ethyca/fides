import { SettingsAdjust } from "@carbon/icons-react";
import { TableProps } from "antd/es/table";
import { Table } from "antd/lib";
import React from "react";

import palette from "../palette/palette.module.scss";
import { PAGE_SIZES } from "./CustomPagination";

// Filter icon component for consistent styling
const FilterIcon = (filtered: boolean) => (
  <SettingsAdjust
    style={{
      color: filtered ? palette.FIDESUI_MINOS : palette.FIDESUI_NEUTRAL_500,
      width: "14px",
    }}
  />
);

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Table component.
 *
 * Default customizations:
 * - Uses "small" size for more compact rows
 * - Enables bordered styling for better visual separation
 * - Uses Carbon SettingsAdjust icon for table column filters
 * - Automatically hides pagination when there's only one page
 * - Uses CustomPagination defaults (showSizeChanger=true, consistent PAGE_SIZES)
 *
 */
export const CustomTable = <RecordType = any,>({
  size = "small",
  bordered = true,
  columns,
  pagination,
  dataSource,
  scroll = { scrollToFirstRowOnChange: true, x: "max-content" },
  ...props
}: TableProps<RecordType>) => {
  // Enhance columns with custom filter icon if they have filters
  const enhancedColumns = React.useMemo(() => {
    if (!columns) {
      return columns;
    }

    return columns.map((column) => {
      // If column has filters but no custom filterIcon, add our Carbon filter icon
      if (column.filters && !column.filterIcon) {
        return {
          ellipsis: true,
          filterIcon: FilterIcon,
          fontSize: "sm",
          ...column,
        };
      }
      return column;
    });
  }, [columns]);

  // Handle pagination logic - hide pagination if there's only one page
  const enhancedPagination = React.useMemo(() => {
    if (pagination === false || !pagination) {
      return pagination;
    }

    // If pagination is true or an object, check if we should hide it
    const pageSize =
      typeof pagination === "object" ? (pagination.pageSize ?? 10) : 10; // Default Ant Design page size
    const total =
      typeof pagination === "object"
        ? (pagination.total ?? dataSource?.length ?? 0)
        : (dataSource?.length ?? 0);

    // If total items fit in one page, hide pagination
    if (total <= pageSize) {
      return false;
    }

    // If pagination should be shown, apply CustomPagination defaults
    const paginationConfig = typeof pagination === "object" ? pagination : {};

    return {
      // Apply CustomPagination defaults first
      showSizeChanger: true,
      pageSizeOptions: PAGE_SIZES.map(String),
      // Then apply any user-provided config (allows overriding defaults)
      ...paginationConfig,
    };
  }, [pagination, dataSource]);

  return (
    <Table
      size={size}
      bordered={bordered}
      columns={enhancedColumns}
      pagination={enhancedPagination}
      dataSource={dataSource}
      scroll={scroll}
      {...props}
    />
  );
};
