import { SettingsAdjust } from "@carbon/icons-react";
import { TableProps } from "antd/es/table";
import { Table } from "antd/lib";
import React from "react";

import palette from "../palette/palette.module.scss";

// Filter icon component for consistent styling
const FilterIcon = () => (
  <SettingsAdjust
    style={{
      color: palette.FIDESUI_NEUTRAL_500,
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
 *
 */
export const CustomTable = <RecordType = any,>({
  size = "small",
  bordered = true,
  columns,
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
          ...column,
          filterIcon: FilterIcon,
        };
      }
      return column;
    });
  }, [columns]);

  return (
    <Table
      size={size}
      bordered={bordered}
      columns={enhancedColumns}
      {...props}
    />
  );
};
