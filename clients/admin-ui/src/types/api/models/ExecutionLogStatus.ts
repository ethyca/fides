/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for execution log statuses, reflecting where they are in their workflow
 */
export enum ExecutionLogStatus {
  IN_PROCESSING = "in_processing",
  PENDING = "pending",
  COMPLETE = "complete",
  ERROR = "error",
  PAUSED = "paused",
  RETRYING = "retrying",
  SKIPPED = "skipped",
}
