import { ExecutionGraphNodeStatus } from "../types";

export const EXECUTION_GRAPH_STATUS_LABELS: Record<
  ExecutionGraphNodeStatus,
  string
> = {
  queued: "Queued",
  executing: "Executing",
  complete: "Complete",
  error: "Error",
  skipped: "Skipped",
  retrying: "Retrying",
  paused: "Paused",
  polling: "Polling",
};

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
