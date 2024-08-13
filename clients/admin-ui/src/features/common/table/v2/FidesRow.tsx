import { Row } from "@tanstack/react-table";
import { Tooltip, Tr } from "fidesui";

import { FidesCell } from "~/features/common/table/v2/FidesCell";

type Props<T> = {
  row: Row<T>;
  onRowClick?: (row: T, e: React.MouseEvent<HTMLTableCellElement>) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
  displayAllColumns: string[];
};

export const FidesRow = <T,>({
  row,
  renderRowTooltipLabel,
  onRowClick,
  displayAllColumns,
}: Props<T>) => {
  if (row.getIsGrouped()) {
    return null;
  }
  const rowEl = (
    <Tr
      height="36px"
      _hover={onRowClick ? { backgroundColor: "neutral.50" } : undefined}
      key={row.id}
      data-testid={`row-${row.id}`}
      backgroundColor={row.getCanSelect() ? undefined : "neutral.50"}
    >
      {row.getVisibleCells().map((cell) => (
        <FidesCell
          key={cell.id}
          cell={cell}
          onRowClick={onRowClick}
          isDisplayAll={!!displayAllColumns.find((c) => c === cell.column.id)}
        />
      ))}
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
