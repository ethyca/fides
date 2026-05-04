import { CSSProperties } from "react";

import { CardSpec } from "./types";

export const RADAR_LAYOUT = {
  splash: {
    width: "min(85vw, 600px)",
    chartSize: "min(80vh, 600px)",
  },
  explore: {
    paneWidthVw: 40,
    width: "min(80%, 480px)",
  },
  transition: {
    duration: 0.6,
    ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
  },
} as const;

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
