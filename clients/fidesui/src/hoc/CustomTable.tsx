import { ColumnsType } from "antd/es/table";
import { MenuProps, Table, TableProps } from "antd/lib";
import React from "react";

import { CustomTableHeaderCell } from "./CustomTableHeaderCell";

type CustomColumnType<RecordType = any> = ColumnsType<RecordType>[number] & {
  menu?: MenuProps;
};

export type CustomColumnsType<RecordType = any> =
  CustomColumnType<RecordType>[];

export type CustomTableProps<RecordType = any> = Omit<
  TableProps<RecordType>,
  "columns"
> & {
  columns: CustomColumnsType<RecordType>;
};

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Table component.
 *
 * Default customizations:
 * - Uses "small" size for more compact rows
 * - Enables bordered styling for better visual separation
 * - Automatically hides pagination when there's only one page
 *
 */
export const CustomTable = <RecordType = any,>({
  size = "small",
  bordered = true,
  pagination,
  dataSource,
  components,
  columns,
  scroll = { scrollToFirstRowOnChange: true, x: "max-content" },
  ...props
}: CustomTableProps<RecordType>) => {
  const paginationDefaults = React.useMemo(() => {
    if (pagination === false || !pagination) {
      return pagination;
    }

    return {
      showSizeChanger: true,
      hideOnSinglePage:
        pagination.pageSize?.toString() ===
        pagination.pageSizeOptions?.[0]?.toString(), // Hide pagination if there's only one page
      ...pagination,
    };
  }, [pagination, dataSource]);

  const customColumns = React.useMemo(() => {
    return columns.map((column) => ({
      ...column,
      onHeaderCell: (data: any, index: number) => {
        // Get existing onHeaderCell props if they exist
        const existingProps = column.onHeaderCell?.(data, index) || {};

        // Merge with our menu prop
        return {
          ...existingProps,
          menu: column.menu,
        };
      },
    }));
  }, [columns]);

  return (
    <Table
      size={size}
      bordered={bordered}
      pagination={paginationDefaults}
      dataSource={dataSource}
      scroll={scroll}
      rowSelection={rowSelection}
      {...props}
      components={{
        header: {
          ...components?.header,
          cell: CustomTableHeaderCell,
        },
        ...components,
      }}
      columns={customColumns as ColumnsType<RecordType>}
    />
  );
};
