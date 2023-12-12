import { Td } from "@fidesui/react";
import { flexRender, Cell } from "@tanstack/react-table";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

type FidesCellProps<T> = {
  cell: Cell<T, unknown>;
  onRowClick?: (row: T) => void;
};

export const FidesCell = <T,>({ cell, onRowClick }: FidesCellProps<T>) => {
  // this should be a custom grouping cell. This logic shouldn't run for every cell
  let isFirstRowOfGroupedRows = false;
  let isLastRowOfGroupedRows = false;
  const rows = cell
    .getContext()
    .table.getRowModel()
    .rows.filter((r) => !r.id.includes(":"));
  let isFirstRowOfPage = rows[0].id === cell.row.id;
  let isLastRowOfPage = rows[rows.length - 1].id == cell.row.id;
  if (cell.getValue() && cell.column.id == "systemName") {
    console.log(cell.getIsGrouped());
    const groupRow = cell
      .getContext()
      .table.getRow(`${cell.column.id}:${cell.getValue()}`);
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
      borderBottomWidth={
        isLastRowOfPage || cell.column.id === "systemName" ? "0px" : "1px"
      }
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
          (cell.getContext().table.getState().grouping.length == 0 &&
            !isLastRowOfPage) ||
          (isLastRowOfGroupedRows && !isFirstRowOfPage)
            ? "1px"
            : "0px",
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
