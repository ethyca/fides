/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Updates dictionary for datastore monitors with classification and review counts
 */
export type DatastoreMonitorUpdates = {
  unlabeled: number;
  in_review: number;
  classifying: number;
  removals: number;
  approved: number;
  classified_low_confidence: number;
  classified_high_confidence: number;
  classified_manually: number;
};
