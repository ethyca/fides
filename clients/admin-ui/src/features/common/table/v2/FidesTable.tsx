import {
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import {
  flexRender,
  RowData,
  Table as TableInstance,
} from "@tanstack/react-table";
import React, { ReactNode } from "react";

const getTableTHandTDStyles = (cellId: string) =>
  cellId === "select"
    ? { padding: "0px" }
    : {
        paddingLeft: "16px",
        paddingRight: "8px",
        paddingTop: "0px",
        paddingBottom: "0px",
      };

/*
  This was throwing a false positive for unused parameters.
  It's also how the library author recommends typing meta.
  https://tanstack.com/table/v8/docs/api/core/column-def#meta
*/
/* eslint-disable */
declare module "@tanstack/table-core" {
  interface ColumnMeta<TData extends RowData, TValue> {
    width?: string;
    minWidth?: string;
    maxWidth?: string;
  }
}
/* eslint-enable */

type Props<T> = {
  tableInstance: TableInstance<T>;
  rowActionBar?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
};

export const FidesTableV2 = <T,>({
  tableInstance,
  rowActionBar,
  footer,
  onRowClick,
}: Props<T>) => (
  <TableContainer
    data-testid="fidesTable"
    overflowY="auto"
    borderBottomWidth="1px"
    borderBottomColor="gray.200"
  >
    <Table
      variant="unstyled"
      style={{
        borderCollapse: "separate",
        borderSpacing: 0,
      }}
    >
      <Thead
        position="sticky"
        top="0"
        height="36px"
        zIndex={10}
        backgroundColor="gray.50"
      >
        {tableInstance.getHeaderGroups().map((headerGroup) => (
          <Tr key={headerGroup.id} height="inherit">
            {headerGroup.headers.map((header) => (
              <Th
                key={header.id}
                borderTopWidth="1px"
                borderTopColor="gray.200"
                borderBottomWidth="1px"
                borderBottomColor="gray.200"
                borderRightWidth="1px"
                borderRightColor="gray.200"
                _first={{
                  borderLeftWidth: "1px",
                  borderLeftColor: "gray.200",
                }}
                colSpan={header.colSpan}
                data-testid={`column-${header.id}`}
                style={{
                  ...getTableTHandTDStyles(header.column.id),
                  width: header.column.columnDef.meta?.width || "unset",
                  minWidth: header.column.columnDef.meta?.minWidth || "unset",
                  maxWidth: header.column.columnDef.meta?.maxWidth || "unset",
                }}
                textTransform="unset"
              >
                {flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )}
              </Th>
            ))}
          </Tr>
        ))}
      </Thead>
      <Tbody data-testid="fidesTable-body">
        {rowActionBar}
        {tableInstance.getRowModel().rows.map((row) => (
          <Tr
            key={row.id}
            height="36px"
            _hover={
              onRowClick
                ? { backgroundColor: "gray.50", cursor: "pointer" }
                : undefined
            }
            data-testid={`row-${row.id}`}
            backgroundColor={row.getCanSelect() ? undefined : "gray.50"}
          >
            {row.getVisibleCells().map((cell) => (
              <Td
                key={cell.id}
                width={
                  cell.column.columnDef.meta?.width
                    ? cell.column.columnDef.meta.width
                    : "unset"
                }
                borderBottomWidth="1px"
                borderBottomColor="gray.200"
                borderRightWidth="1px"
                borderRightColor="gray.200"
                _first={{
                  borderLeftWidth: "1px",
                  borderLeftColor: "gray.200",
                }}
                height="inherit"
                style={getTableTHandTDStyles(cell.column.id)}
                onClick={
                  cell.column.columnDef.header !== "Enable" && onRowClick
                    ? () => {
                        onRowClick(row.original);
                      }
                    : undefined
                }
              >
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </Td>
            ))}
          </Tr>
        ))}
      </Tbody>
      {footer}
    </Table>
  </TableContainer>
);
