import {
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tooltip,
  Tr,
} from "@fidesui/react";
import {
  flexRender,
  Row,
  Cell,
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

type FidesCellProps<T> = {
  cell: Cell<T, unknown>;
  onRowClick?: (row: T) => void;
};

const FidesCell = <T,>({ cell, onRowClick }: FidesCellProps<T>) => {
  // this should be a custom grouping cell. This logic shouldn't run for every cell
  let isFirstRowOfGroupedRows = false;
  if(cell.getValue() && cell.column.id == "systemName"){
    const groupRow = cell.getContext().table.getRow(`${cell.column.id}:${cell.getValue()}`)    
    // console.log(groupRow.subRows)
    isFirstRowOfGroupedRows = groupRow.subRows[0].id === cell.row.id;
  }
  return (
    <Td
      key={cell.id}
      width={
        cell.column.columnDef.meta?.width
          ? cell.column.columnDef.meta.width
          : "unset"
      }
      borderBottomWidth={cell.column.id === "systemName"? "0px": "1px"}
      borderTopWidth={cell.column.id === "systemName" && isFirstRowOfGroupedRows? "1px": "0px"}
      borderBottomColor="gray.200"
      borderRightWidth="1px"
      borderRightColor="gray.200"
      _first={{
        // borderTopWidth: "0px",
        borderLeftWidth: "1px",
        borderLeftColor: "gray.200",
      }}
      height="inherit"
      style={{
        ...getTableTHandTDStyles(cell.column.id),
        background: cell.getIsGrouped()
          ? "#0aff0082"
          : cell.getIsAggregated()
          ? "#ffa50078"
          : cell.getIsPlaceholder()
          ? "unset"
          : "white",
      }}
      onClick={
        cell.column.columnDef.header !== "Enable" && onRowClick
          ? () => {
              onRowClick(row.original);
            }
          : undefined
      }
    >
      {cell.getIsGrouped() || isFirstRowOfGroupedRows
        ? flexRender(cell.column.columnDef.cell, cell.getContext())
        : cell.getIsAggregated()
        ? flexRender(cell.column.columnDef.cell, cell.getContext())
        : cell.getIsPlaceholder()
        ? null
        : flexRender(cell.column.columnDef.cell, cell.getContext())}
    </Td>
  );
};

type FidesRowProps<T> = {
  row: Row<T>;
  onRowClick?: (row: T) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
};

const FidesRow = <T,>({
  row,
  renderRowTooltipLabel,
  onRowClick,
}: FidesRowProps<T>) => {
  if(row.getIsGrouped()){
    return null
  }
  console.log(row.getParentRows())
  // console.log(row.getIsGrouped())
  const rowEl = (
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
        <FidesCell cell={cell} onRowClick={onRowClick} />
      ))}
    </Tr>
  );
  if (renderRowTooltipLabel) {
    return (
      <Tooltip
        key={`tooltip-${row.id}`}
        label={renderRowTooltipLabel ? renderRowTooltipLabel(row) : undefined}
        hasArrow
        placement="top"
      >
        {rowEl}
      </Tooltip>
    );
  }
  return rowEl;
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
          <FidesRow<T> row={row} />
        ))}
      </Tbody>
      {footer}
    </Table>
  </TableContainer>
);
