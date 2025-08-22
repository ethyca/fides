import { ColumnsType } from "antd/es/table";
import { MenuProps, Table, TableProps } from "antd/lib";
import React from "react";
import { ResizeCallbackData } from "react-resizable";

import { CustomTableHeaderCell } from "./CustomTableHeaderCell";

type CustomColumnType<RecordType = any> = ColumnsType<RecordType>[number] & {
  menu?: MenuProps;
  disableResize?: boolean;
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
  const [newColumns, setNewColumns] = React.useState(columns);

  React.useEffect(() => {
    setNewColumns(columns);
  }, [columns]);

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

  const handleResize =
    (index: number) =>
    (_: React.SyntheticEvent<Element>, data: ResizeCallbackData) => {
      setNewColumns((cols) => {
        const nextColumns = [...cols];
        if (nextColumns[index]) {
          nextColumns[index].width = data.size.width;
        }
        return nextColumns;
      });
    };

  const customColumns = React.useMemo(() => {
    return newColumns.map((column, index: number) => ({
      ...column,
      onHeaderCell: (data: React.HTMLAttributes<HTMLTableCellElement>) => {
        // Get existing onHeaderCell props if they exist
        const existingProps = column.onHeaderCell?.(data) || {};

        // Merge with our menu prop
        return {
          ...existingProps,
          menu: column.menu,
          disableResize: column.disableResize,
          width: column.width,
          onResize: handleResize(index),
        };
      },
    }));
  }, [columns, newColumns]);

  return (
    <Table
      size={size}
      bordered={bordered}
      pagination={paginationDefaults}
      dataSource={dataSource}
      scroll={scroll}
      {...props}
      components={{
        ...components,
        header: {
          ...components?.header,
          cell: CustomTableHeaderCell,
        },
      }}
      columns={customColumns as unknown as ColumnsType<RecordType>}
    />
  );
};
