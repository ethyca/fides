import { Td } from "@fidesui/react";
import { flexRender, Cell } from "@tanstack/react-table";

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

export const FidesCell = <T,>({ cell, onRowClick }: FidesCellProps<T>) => {
  // this should be a custom grouping cell. This logic shouldn't run for every cell
  let isFirstRowOfGroupedRows = false;
  if (cell.getValue() && cell.column.id == "systemName") {
    const groupRow = cell
      .getContext()
      .table.getRow(`${cell.column.id}:${cell.getValue()}`);
    isFirstRowOfGroupedRows = groupRow.subRows[0].id === cell.row.id;
  }
  return (
    <Td
      width={
        cell.column.columnDef.meta?.width
          ? cell.column.columnDef.meta.width
          : "unset"
      }
      borderBottomWidth={cell.column.id === "systemName" ? "0px" : "1px"}
      borderTopWidth={
        cell.column.id === "systemName" && isFirstRowOfGroupedRows
          ? "1px"
          : "0px"
      }
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
