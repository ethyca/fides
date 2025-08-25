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
  onColumnResize?: (columnKey: string, width: number) => void;
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
  onColumnResize,
  scroll = { scrollToFirstRowOnChange: true, x: "max-content" },
  ...props
}: CustomTableProps<RecordType>) => {
  const [columnWidths, setColumnWidths] = React.useState<
    Record<string, number>
  >({});

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
    (columnKey: string) =>
    (_: React.SyntheticEvent<Element>, data: ResizeCallbackData) => {
      // Update local width state for immediate UI feedback
      setColumnWidths((prev) => ({
        ...prev,
        [columnKey]: data.size.width,
      }));

      // Call the onColumnResize callback if provided
      if (onColumnResize) {
        onColumnResize(columnKey, data.size.width);
      }
    };

  const customColumns = React.useMemo(() => {
    return columns.map((column) => {
      const columnKey = String(column.key);
      // Use local width if available, otherwise fall back to column width
      const currentWidth = columnWidths[columnKey] ?? column.width;

      return {
        ...column,
        width: currentWidth,
        onHeaderCell: (data: React.HTMLAttributes<HTMLTableCellElement>) => {
          // Get existing onHeaderCell props if they exist
          const existingProps = column.onHeaderCell?.(data) || {};

          // Merge with our menu prop
          return {
            ...existingProps,
            menu: column.menu,
            disableResize: column.disableResize,
            width: currentWidth,
            onResize: handleResize(columnKey),
          };
        },
      };
    });
  }, [columns, columnWidths, handleResize]);

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
