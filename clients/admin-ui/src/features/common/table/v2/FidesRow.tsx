import { Tooltip, Tr } from "@fidesui/react";
import { Row } from "@tanstack/react-table";

import { FidesCell } from "~/features/common/table/v2/FidesCell";

type Props<T> = {
  row: Row<T>;
  onRowClick?: (row: T) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
};

export const FidesRow = <T,>({
  row,
  renderRowTooltipLabel,
  onRowClick,
}: Props<T>) => {
  if (row.getIsGrouped()) {
    return null;
  }
  const rowEl = (
    <Tr
      height="36px"
      _hover={
        onRowClick
          ? { backgroundColor: "gray.50", cursor: "pointer" }
          : undefined
      }
      key={row.id}
      data-testid={`row-${row.id}`}
      backgroundColor={row.getCanSelect() ? undefined : "gray.50"}
    >
      {row.getVisibleCells().map((cell) => (
        <FidesCell key={cell.id} cell={cell} onRowClick={onRowClick} />
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
