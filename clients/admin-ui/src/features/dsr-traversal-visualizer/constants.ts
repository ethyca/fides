export const NODE_WIDTH = 240;
// Matches the rendered height of an integration card with our pinned chip
// row. Dagre uses this to allocate vertical space in the LR layout -- if
// it lags the real height, sibling cards crowd together and the spacing
// between stacked nodes reads as inconsistent.
export const NODE_HEIGHT = 160;

export const NODE_TYPES = {
  IDENTITY_ROOT: "identityRoot",
  INTEGRATION: "integration",
  MANUAL_TASK: "manualTask",
} as const;

export const EDGE_TYPES = {
  DEPENDENCY: "dependency",
  GATES: "gates",
} as const;

export const REACHABILITY_LABEL = {
  reachable: "Reachable",
  unreachable: "Unreachable",
  requires_manual_identity: "Needs manual ID",
} as const;

export const REACHABILITY_COLOR = {
  reachable: "success",
  unreachable: "default",
  requires_manual_identity: "warning",
} as const;

// Lane layout — pixel coordinates and widths used by computeLaneLayout.
export const LANE_X = {
  identity: 0,
  reach: 320,
  gated: 0, // computed at runtime — depends on reach lane width
  skipped: 0, // computed at runtime — depends on gated lane width
} as const;

export const LANE_Y_TOP = 0;

// Cards stack vertically with this pitch (card height + gap between rows).
export const CARD_PITCH = NODE_HEIGHT + 20;

// Width of a single column inside a lane (card + horizontal gap between cols).
export const COL_WIDTH = NODE_WIDTH + 16;

// Horizontal padding on each side of a lane — keeps cards from sitting flush
// against the lane border and gives the chrome breathing room.
export const LANE_PADDING_X = 14;

// Vertical breathing room at the bottom of a lane after the last card.
export const LANE_PADDING_BOTTOM = 16;

// Multi-column promotion thresholds. >MAX_SINGLE_COL → 2-col, >MAX_DOUBLE_COL → 3-col.
export const LANE_SINGLE_COL_MAX = 5;
export const LANE_DOUBLE_COL_MAX = 12;

// Maximum columns supported per lane.
export const MAX_LANE_COLS = 3;

// Vertical gap between stage sub-sections inside the reach lane.
export const STAGE_GAP = 28;

// Header reserves vertical space at the top of each lane (header bar + gap
// below it before the first card).
export const LANE_HEADER_HEIGHT = 48;

// Stage sub-header reserves vertical space inside a lane. Tall enough that
// labels which wrap to two lines (narrow lanes) don't overlap the cards
// below them.
export const STAGE_HEADER_HEIGHT = 40;

// Width of a collapsed lane (just the rotated label + count chip).
export const COLLAPSED_LANE_WIDTH = 44;

// Inter-lane gap (between lane right edge and the next lane's left edge).
export const LANE_GAP = 56;

// Where useLaneCollapseState persists user preferences.
export const LANE_COLLAPSE_STORAGE_KEY = "fides:dsr-traversal:lane-collapse:v1";

export type LaneId = "identity" | "reach" | "gated" | "skipped";

export const LANE_IDS: readonly LaneId[] = [
  "identity",
  "reach",
  "gated",
  "skipped",
] as const;
