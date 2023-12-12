import { Table, TableContainer, Tbody, Th, Thead, Tr } from "@fidesui/react";
import {
  flexRender,
  Row,
  RowData,
  Table as TableInstance,
} from "@tanstack/react-table";
import React, { ReactNode } from "react";
import { FidesRow } from "~/features/common/table/v2/FidesRow";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

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
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
};

export const FidesTableV2 = <T,>({
  tableInstance,
  rowActionBar,
  footer,
  onRowClick,
  renderRowTooltipLabel,
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
          <FidesRow<T> key={row.id} row={row} />
        ))}
      </Tbody>
      {footer}
    </Table>
  </TableContainer>
);
