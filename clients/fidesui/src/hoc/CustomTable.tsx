import { TableProps } from "antd/es/table";
import { Table } from "antd/lib";
import React from "react";

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Table component.
 *
 * Default customizations:
 * - Uses "small" size for more compact rows
 * - Enables bordered styling for better visual separation
 *
 */
export const CustomTable = <RecordType = any,>({
  size = "small",
  bordered = true,
  ...props
}: TableProps<RecordType>) => {
  return <Table size={size} bordered={bordered} {...props} />;
};
