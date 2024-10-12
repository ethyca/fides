import { Cell, flexRender } from "@tanstack/react-table";
import { Td } from "fidesui";

import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

export interface FidesCellState {
  isExpanded?: boolean;
  isWrapped?: boolean;
  version?: number;
}

export interface FidesCellProps<T> {
  cell: Cell<T, unknown>;
  onRowClick?: (row: T, e: React.MouseEvent<HTMLTableCellElement>) => void;
  cellState?: FidesCellState;
}

export const FidesCell = <T,>({
  cell,
  onRowClick,
  cellState,
}: FidesCellProps<T>) => {
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
  const hasCellClickEnabled =
    (!isGroupedColumn || isFirstRowOfGroupedRows) &&
    !!cell.column.columnDef.meta?.onCellClick;
  let handleCellClick;
  if (!cell.column.columnDef.meta?.disableRowClick && onRowClick) {
    handleCellClick = (e: React.MouseEvent<HTMLTableCellElement>) => {
      onRowClick(cell.row.original, e);
    };
  } else if (hasCellClickEnabled) {
    handleCellClick = () => {
      cell.column.columnDef.meta?.onCellClick?.(cell.row.original);
    };
  }

  return (
    <Td
      width={
        cell.column.columnDef.meta?.width
          ? cell.column.columnDef.meta.width
          : "unset"
      }
      overflow={
        cell.column.columnDef.meta?.overflow
          ? cell.column.columnDef.meta?.overflow
          : "auto"
      }
      borderBottomWidth={isLastRowOfPage || isGroupedColumn ? "0px" : "1px"}
      borderBottomColor="gray.200"
      borderRightWidth="1px"
      borderRightColor="gray.200"
      sx={{
        article: {
          borderTopWidth: "2x",
          borderTopColor: "red",
        },
        ...getTableTHandTDStyles(cell.column.id),
        // Fancy CSS memoization magic https://tanstack.com/table/v8/docs/framework/react/examples/column-resizing-performant
        maxWidth: `calc(var(--col-${cell.column.id}-size) * 1px)`,
        minWidth: `calc(var(--col-${cell.column.id}-size) * 1px)`,
        "&:hover": {
          backgroundColor: hasCellClickEnabled ? "gray.50" : undefined,
          cursor: hasCellClickEnabled ? "pointer" : undefined,
        },
      }}
      _hover={
        onRowClick && !cell.column.columnDef.meta?.disableRowClick
          ? { cursor: "pointer" }
          : undefined
      }
      _first={{
        borderBottomWidth:
          (!isTableGrouped && !isLastRowOfPage) ||
          (isLastRowOfGroupedRows && !isFirstRowOfPage) ||
          (isFirstRowOfGroupedRows && hasOneSubRow)
            ? "1px"
            : "0px",
      }}
      _last={{
        borderRightWidth: 0,
      }}
      height="inherit"
      onClick={handleCellClick}
      data-testid={`row-${cell.row.id}-col-${cell.column.id}`}
    >
      {!cell.getIsPlaceholder() || isFirstRowOfGroupedRows
        ? flexRender(cell.column.columnDef.cell, {
            ...cell.getContext(),
            cellState,
          })
        : null}
    </Td>
  );
};
