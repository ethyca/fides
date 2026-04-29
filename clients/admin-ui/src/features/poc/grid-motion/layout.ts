import { CSSProperties } from "react";

import { CardSpec } from "./types";

export const getCardStyle = (
  spec: CardSpec,
  isExpanded: boolean,
  colCount?: number,
): CSSProperties => {
  const { cols, rows } = isExpanded ? spec.expanded : spec.collapsed;
  const effectiveCols =
    colCount && colCount > 0 && cols >= colCount - 1 ? colCount : cols;
  return {
    gridColumn: `span ${effectiveCols}`,
    gridRow: `span ${rows}`,
  };
};
