import { CSSProperties } from "react";

import { CardSpec } from "./types";

export const getCardStyle = (
  spec: CardSpec,
  isExpanded: boolean,
): CSSProperties => {
  const { cols, rows } = isExpanded ? spec.expanded : spec.collapsed;
  return {
    gridColumn: `span ${cols}`,
    gridRow: `span ${rows}`,
  };
};
