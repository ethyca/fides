import { Td } from "@fidesui/react";
import { Cell, flexRender } from "@tanstack/react-table";

import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

type FidesCellProps<T> = {
  cell: Cell<T, unknown>;
  onRowClick?: (row: T) => void;
};

export const FidesCell = <T,>({ cell, onRowClick }: FidesCellProps<T>) => {
  const isTableGrouped = cell.getContext().table.getState().grouping.length > 0;
  const groupedColumnId = isTableGrouped
    ? cell.getContext().table.getState().grouping[0]
    : undefined;
  const isGroupedColumn = cell.column.id === groupedColumnId;
  let isFirstRowOfGroupedRows = false;
  let isLastRowOfGroupedRows = false;
  let hasOneSubRow = false;
  const rows = cell
    .getContext()
    .table.getRowModel()
    .rows.filter((r) => !r.id.includes(":"));
  const isFirstRowOfPage = rows[0].id === cell.row.id;
  const isLastRowOfPage = rows[rows.length - 1].id === cell.row.id;
  if (cell.getValue() && isGroupedColumn) {
    const groupRow = cell
      .getContext()
      .table.getRow(`${cell.column.id}:${cell.getValue()}`);
    hasOneSubRow = groupRow.subRows.length === 1;
    isFirstRowOfGroupedRows = groupRow.subRows[0].id === cell.row.id;
    isLastRowOfGroupedRows =
      groupRow.subRows[groupRow.subRows.length - 1].id === cell.row.id;
  }

  return (
    <Td
      width={
        cell.column.columnDef.meta?.width
          ? cell.column.columnDef.meta.width
          : "unset"
      }
      maxWidth={cell.column.getCanResize() ? cell.column.getSize() : "unset"}
      overflowX="auto"
      borderBottomWidth={isLastRowOfPage || isGroupedColumn ? "0px" : "1px"}
      borderBottomColor="gray.200"
      borderRightWidth="1px"
      borderRightColor="gray.200"
      sx={{
        article: {
          borderTopWidth: "2x",
          borderTopColor: "red",
        },
      }}
      _first={{
        borderBottomWidth:
          (!isTableGrouped && !isLastRowOfPage) ||
          (isLastRowOfGroupedRows && !isFirstRowOfPage) ||
          (isFirstRowOfGroupedRows && hasOneSubRow)
            ? "1px"
            : "0px",
        borderLeftWidth: "1px",
        borderLeftColor: "gray.200",
      }}
      height="inherit"
      style={{
        ...getTableTHandTDStyles(cell.column.id),
      }}
      onClick={
        cell.column.columnDef.header !== "Enable" && onRowClick
          ? () => {
              onRowClick(cell.row.original);
            }
          : undefined
      }
    >
      {!cell.getIsPlaceholder() || isFirstRowOfGroupedRows
        ? flexRender(cell.column.columnDef.cell, cell.getContext())
        : null}
    </Td>
  );
};
