import { CUSTOM_TAG_COLOR } from "fidesui";

import { LaneId, Reachability } from "./types";

export const NODE_WIDTH = 320;
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

export const REACHABILITY_LABEL: Record<Reachability, string> = {
  [Reachability.REACHABLE]: "Reachable",
  [Reachability.UNREACHABLE]: "Unreachable",
  [Reachability.REQUIRES_MANUAL_IDENTITY]: "Needs manual ID",
};

export const REACHABILITY_COLOR: Record<Reachability, CUSTOM_TAG_COLOR> = {
  [Reachability.REACHABLE]: CUSTOM_TAG_COLOR.SUCCESS,
  [Reachability.UNREACHABLE]: CUSTOM_TAG_COLOR.DEFAULT,
  [Reachability.REQUIRES_MANUAL_IDENTITY]: CUSTOM_TAG_COLOR.WARNING,
};

// Lane layout — pixel coordinates and widths used by computeLaneLayout.
export const LANE_X = {
  identity: 0,
  reach: 320,
  gated: 0, // computed at runtime — depends on reach lane width
  skipped: 0, // computed at runtime — depends on gated lane width
} as const;

export const LANE_Y_TOP = 0;

// Cards stack vertically with this pitch (card height + gap between rows).
// The +70 leaves room for an integration card whose chip row has wrapped to
// up to three lines (each wrapped row adds ~24px) plus a 20px visual gap to
// the next card. The .node SCSS sets min-height to match so cards in the
// same column read as uniformly tall regardless of chip wrap.
export const CARD_PITCH = NODE_HEIGHT + 70;

// Horizontal gap between adjacent columns in a multi-column lane.
export const INTER_COL_GAP = 16;

// Width of a single column slot inside a lane (card + the gap that follows
// it). Used for column-index → x positioning. Only the gap *between*
// columns counts toward the lane's width — see laneWidth() below.
export const COL_WIDTH = NODE_WIDTH + INTER_COL_GAP;

// Horizontal padding on each side of a lane — keeps cards from sitting flush
// against the lane border and gives the chrome breathing room.
export const LANE_PADDING_X = 14;

// Vertical breathing room at the bottom of a lane after the last card.
export const LANE_PADDING_BOTTOM = 16;

// Multi-column promotion thresholds. >MAX_SINGLE_COL → 2-col, >MAX_DOUBLE_COL → 3-col.
// Tuned so a single column never gets taller than ~4 cards before wrapping
// kicks in — keeps tall lanes from scrolling off the viewport.
export const LANE_SINGLE_COL_MAX = 4;
export const LANE_DOUBLE_COL_MAX = 8;

// Maximum columns supported per lane.
export const MAX_LANE_COLS = 3;

// Horizontal gap between consecutive stage blocks inside the reach lane.
// Sized to leave room for the inter-stage flow chevron without ballooning
// the lane.
export const STAGE_GAP_HORIZONTAL = 48;

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

export const LANE_IDS: readonly LaneId[] = [
  LaneId.IDENTITY,
  LaneId.REACH,
  LaneId.GATED,
  LaneId.SKIPPED,
];

// Reserved height for app chrome (top nav + breadcrumb + canvas header)
// subtracted from viewport height when sizing the canvas area.
export const CANVAS_VIEWPORT_OFFSET = 240;
export const CANVAS_HEIGHT_CSS = `calc(100vh - ${CANVAS_VIEWPORT_OFFSET}px)`;
