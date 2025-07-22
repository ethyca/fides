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
      columns={enhancedColumns}
      pagination={paginationDefaults}
      dataSource={dataSource}
      scroll={scroll}
      {...props}
    />
  );
};
