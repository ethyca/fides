import { Row } from "@tanstack/react-table";
import { Tooltip, Tr } from "fidesui";

import {
  FidesCell,
  FidesCellState,
} from "~/features/common/table/v2/FidesCell";

import { columnExpandedVersion } from "./util";

type Props<T> = {
  row: Row<T>;
  onRowClick?: (row: T, e: React.MouseEvent<HTMLTableCellElement>) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
  expandedColumns: string[];
  wrappedColumns: string[];
};

export const FidesRow = <T,>({
  row,
  renderRowTooltipLabel,
  onRowClick,
  expandedColumns,
  wrappedColumns,
}: Props<T>) => {
  if (row.getIsGrouped()) {
    return null;
  }
  const rowEl = (
    <Tr
      height="36px"
      _hover={onRowClick ? { backgroundColor: "gray.50" } : undefined}
      key={row.id}
      data-testid={`row-${row.id}`}
      backgroundColor={row.getCanSelect() ? undefined : "gray.50"}
    >
      {row.getVisibleCells().map((cell) => {
        const expansionVersion = columnExpandedVersion(
          cell.column.id,
          expandedColumns,
        );
        const cellState: FidesCellState = {
          isExpanded: !!expansionVersion && expansionVersion > 0,
          isWrapped: !!wrappedColumns.find((c) => c === cell.column.id),
          version: expansionVersion,
        };
        return (
          <FidesCell
            key={cell.id}
            cell={cell}
            onRowClick={onRowClick}
            cellState={cellState}
          />
        );
      })}
    </Tr>
  );
  if (renderRowTooltipLabel) {
    return (
      <Tooltip
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
