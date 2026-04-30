export const NODE_WIDTH = 240;
export const NODE_HEIGHT = 120;

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
