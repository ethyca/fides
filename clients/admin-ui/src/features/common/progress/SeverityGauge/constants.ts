import { AntProgressProps as ProgressProps } from "fidesui";

import type { Severity } from "./types";

export const SEVERITY_PROPS: Readonly<ProgressProps> = {
  percentPosition: {
    align: "start",
    type: "outer",
  },
  steps: 3,
  strokeLinecap: "round",
  size: {
    width: 24,
    height: 8,
  },
  rounding: Math.ceil,
} as const;

export const SEVERITY_STYLE: Record<Severity, string> = {
  low: "var(--fidesui-error)",
  medium: "var(--fidesui-warning)",
  high: "var(--fidesui-success)",
} as const;

export const SEVERITY_PERCENT: Record<Severity, number> = {
  low: 30,
  medium: 60,
  high: 100,
} as const;
