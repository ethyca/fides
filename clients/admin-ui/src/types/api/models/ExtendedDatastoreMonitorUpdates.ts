/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extends DatastoreMonitorUpdates with approved count for cross-monitor views.
 */
export type ExtendedDatastoreMonitorUpdates = {
  unlabeled: number;
  in_review: number;
  classifying: number;
  removals: number;
  reviewed: number;
  classified_low_confidence: number | null;
  classified_medium_confidence: number | null;
  classified_high_confidence: number | null;
  approved: number;
};
