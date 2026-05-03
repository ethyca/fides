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
