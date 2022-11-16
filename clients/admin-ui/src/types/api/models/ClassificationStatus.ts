/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model housing statuses for a classify instance.
 *
 * CREATED: The initial state of an attempt to classify
 * PROCESSING: Attempting to classify dataset(s)
 * COMPLETE: The classify process completed successfully
 * FAILED: The classify process failed (at some point)
 * REVIEWED: The output classification has been reviewd
 * along with the generated dataset, passed from UI
 */
export enum ClassificationStatus {
  CREATED = "Created",
  PROCESSING = "Processing",
  COMPLETE = "Complete",
  FAILED = "Failed",
  REVIEWED = "Reviewed",
}
