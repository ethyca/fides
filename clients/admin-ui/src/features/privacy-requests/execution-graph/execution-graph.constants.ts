import { ExecutionGraphNodeStatus } from "../types";

export const EXECUTION_GRAPH_STATUS_LABELS: Record<
  ExecutionGraphNodeStatus,
  string
> = {
  pending: "Pending",
  executing: "Executing",
  complete: "Complete",
  error: "Error",
  skipped: "Skipped",
  retrying: "Retrying",
  paused: "Paused",
  polling: "Polling",
};

/**
 * Priority order for aggregate status: higher number = worse status wins.
 * Used to compute the "worst" status across all collections in a dataset.
 */
export const STATUS_PRIORITY: Record<ExecutionGraphNodeStatus, number> = {
  skipped: 0,
  complete: 1,
  pending: 2,
  paused: 3,
  polling: 4,
  retrying: 5,
  executing: 6,
  error: 7,
};

export const DATASET_NODE_WIDTH = 260;
export const DATASET_NODE_HEIGHT = 90;

const ROOT_ADDRESS = "__ROOT__:__ROOT__";
const TERMINATOR_ADDRESS = "__TERMINATE__:__TERMINATE__";

export function isRootNode(collectionAddress: string): boolean {
  return collectionAddress === ROOT_ADDRESS;
}

export function isTerminatorNode(collectionAddress: string): boolean {
  return collectionAddress === TERMINATOR_ADDRESS;
}

export function isInternalNode(collectionAddress: string): boolean {
  return isRootNode(collectionAddress) || isTerminatorNode(collectionAddress);
}
